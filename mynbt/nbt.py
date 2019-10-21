import gzip
from struct import pack, unpack, iter_unpack
from weakref import WeakSet
import collections

import io

class TAG:
    datatypes = {}

    def __init__(self, value = None, parent = None):
        self._payload = None
        self._id = self.__class__.ID
        self._value = value
        self._parents = WeakSet()

    def __repr__(self):
        attr=[]
        if self._payload is not None:
          attr.append("cached")

        return "{tag}({attr})".format(tag=self.__class__.__name__, attr=", ".join(attr))


    def invalidate(self):
        queue = [self]
        while queue:
          item = queue.pop()
          if item._payload:
            item._payload = None
            queue.extend(item._parents)

    def export(self, *, compact=True):
        """ Export a NBT data structure as Python native objects.
        """
        value = self.value

        if compact:
          return value
        else:
          return {
            'type': self.__class__.__name__,
            'value': value,
          }

    @property
    def value(self):
        return self.get_value()

    def get_value(self):
        if self._value is None:
          self._value = self.unpack()

        return self._value

    @staticmethod
    def parse_id(base, offset):
        ID, = unpack('>B',bytes(base[offset:offset+1]))
        return ID,offset+1

    @staticmethod
    def parse_name(base, offset):
        l, = unpack('>h',bytes(base[offset:offset+2]))
        name = bytes(base[offset+2:offset+2+l]).decode("utf8")
        return name,offset+2+l

    @staticmethod
    def parse_tag(base, offset):
        ID,offset = TAG.parse_id(base, offset)
        trait = TraitMetaclass.TRAITS[ID]
        assert trait.ID == ID

        return trait, offset

    @staticmethod
    def parse(base, offset, parent = None):
        base = memoryview(base)
        start = offset
        name = None
        trait, offset = TAG.parse_tag(base,offset)
        if trait is EndTrait:
          result = End(parent=parent)
        else:
          name, offset = TAG.parse_name(base, offset)
          result, offset = trait.make_from_payload(base, offset, parent=parent)

        return result, name, offset

    @staticmethod
    def parse_file(path):
        readers = (
          gzip.open,
          open,
        )
        
        err = None
        for reader in readers:
          try:
            with reader(path, "rb") as f:
              data = f.read()
            break
          except OSError as e:
            err = e
        else:
          raise err or OSError("Can't open " + path)

        result, name, offset = TAG.parse(data, 0)

        assert data[offset:] == b""
        return result

    def write_payload(self, output):
        pass

# ==================================================================== 
# Value types
# ==================================================================== 
class Node:
    """ Base class for NBT node elements.
        When parsing NBT data, node are mostly proxy containing
        the raw undecoded bytes for the node.
        
        When the value of a proxy node is accessed, it instanciates
        a value node
    """
    def __init__(self, *, trait, payload=None, parent = None):
        self._trait = trait
        self._payload = payload
        self._parents = WeakSet()
        if parent is not None:
            self.register_parent(parent)

    def register_parent(self,parent):
        assert isinstance(parent, Node), "Parent must be  valid NBT node " + str(type(parent))
        self._parents.add(parent)

    def register_parents(self,parents):
        for parent in parents:
            self.register_parent(parent)
        return self

    def invalidate(self):
        queue = [self]
        while queue:
          item = queue.pop()
          if item._payload:
            item._payload = None
            queue.extend(item._parents)

    #------------------------------------
    # Exporting NBT values
    #------------------------------------
    def write(self, output, name=""):
        """ Write the NBT object to a file-like output.
            The output is assumed to be a binary stream
        """
        # XXX rename me to write_into or write_to or dump_to
        output.write(self._trait.ID.to_bytes(1, 'big'))
        if name is not None:
            output.write(len(name).to_bytes(2, 'big'))
            output.write(name.encode('utf8'))

        if self._payload is not None:
            output.write(self._payload)
        else:
            self.write_payload(output)

    def dump(self, name=""):
        output = io.BytesIO()
        self.write(output, name)
        return output.getbuffer()

    def write_payload(self, output):
        if self._payload is None:
            raise ValueError

        output.write(self._payload)

    def export(self, *, compact=True):
        raise NotImplementedError

    def value(self):
        return self

# ==================================================================== 
# Value types
# ==================================================================== 
class End(Node):
    def __init__(self, *, parent):
      super().__init__(trait=EndTrait, parent=parent)

class Value(Node):
    def write_payload(self, output):
        if self._payload is None:
            self._payload = self.pack()

        super().write_payload(output)

    def pack(self):
        """ Pack the value to a proper byte payload
            
            This implementation assume `self` is
            a subclass of a native Python type
        """
        return pack(self._trait.FORMAT, self) 

class Integer(int, Value):
    def __new__(cls, value, **kwargs):
        return int.__new__(cls, value)

    def __init__(self, value, *, trait = None, payload = None, parent = None):
        Node.__init__(self, trait = trait or IntTrait, payload = payload, parent = parent)

class Float(float, Value):
    def __new__(cls, value, **kwargs):
        return float.__new__(cls, value)

    def __init__(self, value, *, trait = None, payload = None, parent = None):
        Node.__init__(self, trait = trait or DoubleTrait, payload = payload, parent = parent)

class String(str, Value):
    def __new__(cls, value, **kwargs):
        return str.__new__(cls, value)

    def __init__(self, value, *, trait = None, payload = None, parent = None):
        Node.__init__(self, trait = trait or StringTrait, payload = payload, parent = parent)

# ==================================================================== 
# Proxy
# ==================================================================== 
class Proxy(Node):
    """ A proxy stores binary NBT data as read from a binary stream
        (i.e. without decoding them)

        This avoid spending time decoding uneeded data. It also
        speed-up writing back unmodified data
    """
    def __repr__(self):
        return repr("{base}[{trait},{payload}]".format(base=super().__repr__(), trait=self._trait, payload=self._payload))

    #------------------------------------
    # Rich comparisons
    #------------------------------------
    def __eq__(self, other):
        if self is other:
            return True

        if isinstance(other, Proxy):
            other = other.value()

        return self.value() == other

    #------------------------------------
    # Proxy interface
    #------------------------------------
    def unpack(self):
        """ Decode the proxy payload and return proper object
        """
        raise NotImplementedError

    def value(self):
        """ Return a value object corresponding to the payload
        """
        return self._trait.VALUE(self.unpack(), payload=self._payload, trait=self._trait)

    def write_payload(self, output):
        output.write(self._payload)

class AtomProxy(Proxy):
    def unpack(self):
        return unpack(self._trait.FORMAT, self._payload)[0]

class ArrayProxy(Proxy):
    def unpack(self):
        return iter_unpack(self._trait.FORMAT, self._payload[4:])

class StringProxy(Proxy):
    def unpack(self):
        return bytes(self._payload[2:]).decode("utf8") # XXX unneeded (?) copy

class ListNode(Node, collections.abc.MutableSequence, collections.abc.Hashable):
    def __init__(self, *, trait, payload, parent):
        self._items = []
        super().__init__(trait=trait, payload=payload, parent=parent)

    def __repr__(self):
        return super().__repr__() + " {" +\
                ", ".join(repr(item) for item in self._items) +\
                "}"
    #------------------------------------
    # Node interface
    #------------------------------------
    def export(self, *, compact=True):
        """ Export a NBT data structure as Python native objects.
        """
        value = [v.export(compact=compact) for v in self._items]

        if compact:
          return value
        else:
          return {
            'type': self.__class__.__name__,
            'value': value
          }

    def write_payload(self, output):
        output.write(len(self._items).to_bytes(4, 'big'))
        for item in self._items:
            item.write(output, name=None)

    #------------------------------------
    # Proxy interface
    #------------------------------------
    def value(self):
        return self

    #------------------------------------
    # Hashable interface
    #------------------------------------
    def __hash__(self):
        return id(self)

    #------------------------------------
    # Mutable sequence interface
    #------------------------------------
    def __getitem__(self, idx):
        node = self._items[idx]
        value = node.value()

        if value is not node:
            value.register_parent(self)
            self._items[idx] = value

        return value

    def __setitem__(self, idx, value):
        self.invalidate()
        value.register_parent(self)
        self._items[idx] = value # XXX should promote native values to TAG_... ?

    def __delitem__(self, idx):
        self.invalidate()
        # using a WeakKeyDictionary we may emulate multibag and remove self
        # from the removed item parent list
        del self._items[idx]

    def __len__(self):
        return len(self._items)

    def insert(self, idx, value):
        self.invalidate()
        self._items.insert(idx, value)

class CompoundNode(Node, collections.abc.MutableMapping, collections.abc.Hashable):
    def __init__(self, *, trait, payload, parent):
        super().__init__(trait=trait, payload=payload, parent=parent)
        self._items = {}

    def __repr__(self):
        return super().__repr__() + " {" +\
                ", ".join(name + ": " + repr(item) for name, item in self._items.items()) +\
                "}"

    #------------------------------------
    # Node interface
    #------------------------------------
    def export(self, *, scope=None, compact=True):
        """ Export a NBT data structure as Python native objects.
        """
        value = {k: v.export(compact=compact) for k, v in self._items.items() if (scope is None) or (k in scope)}

        if compact:
          return value
        else:
          return {
            'type': self.__class__.__name__,
            'value': value
          }

    def write_payload(self, output):
        for name, item in self._items.items():
            item.write(output, name=name)
        output.write(b"\x00")

    #------------------------------------
    # Proxy interface
    #------------------------------------
    def value(self):
        return self

    #------------------------------------
    # Hashable interface
    #------------------------------------
    def __hash__(self):
        return id(self)

    #------------------------------------
    # Mutable mapping interface
    #------------------------------------
    def keys(self):
        return self._items.keys()

    def __getitem__(self, idx):
        node = self._items[idx]
        value = node.value()

        if value is not node:
            value.register_parent(self)
            self._items[idx] = value

        return value

    def __setitem__(self, idx, value):
        self.invalidate()
        if not isinstance(value, Node):
            # Non-Node objects must be promoted.
            # if the new value replace an existing one, the value keep the same type
            # otherwise a compatible type is inferred
            old = self._items.get(idx)
            trait = old._trait if old is not None else TYPE_TO_TRAIT[type(value)]
            value = trait.VALUE(value, trait=trait)

        self._items[idx] = value

    def __delitem__(self, idx):
        self.invalidate()
        del self._items[idx]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return self._items.__iter__()

    #------------------------------------
    # Mutable object interface
    #------------------------------------
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name.startswith("_"):
          object.__setattr__(self,name,value)
        else:
          self[name] = value

    def __delattr__(self, name):
        if name.startswith("_"):
          object.__delattr__(self,name)
        else:
          del self[name]

# ==================================================================== 
# Reader
# ====================================================================
class Reader:
    def __init__(self, trait):
        self._trait = trait

    def make_from_payload(self, base, offset, *, parent):
        """ Create a node using the binary payload starting as base[offset]
        """
        raise NotImplementedError

class AtomReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        payload = base[offset:offset+self._trait.SIZE] 
        return AtomProxy(trait=self._trait, payload=payload, parent=parent),offset+self._trait.SIZE

class ArrayReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        l, = unpack('>i',bytes(base[offset:offset+4]))
        payload = base[offset:offset+4+l*self._trait.SIZE]
        return ArrayProxy(trait=self._trait, payload=payload, parent=parent),offset+4+l*self._trait.SIZE

class StringReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        l, = unpack('>h',bytes(base[offset:offset+2]))
        payload = base[offset+2:offset+2+l]
        return StringProxy(trait=self._trait, payload=payload, parent=parent),offset+2+l

class ListReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        start = offset
        container = ListNode(trait=self._trait, payload=None, parent=parent)

        trait, offset = TAG.parse_tag(base, offset)
        count, = unpack('>i',bytes(base[offset:offset+4]))
        offset += 4
        # XXX Check implications of that statement:
        # """ If the length of the list is 0 or negative, 
        #     the type may be 0 (End) but otherwise it must 
        #     be any other type. """
        #  -- https://wiki.vg/NBT#Specification

        if count < 0:
            count = 0
        items = []
        while count > 0:
          item, offset = trait.make_from_payload(base, offset, parent=container)
          container.append(item)
          count -= 1
        
        container._payload = base[start:offset]
        return container, offset

class CompoundReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        container = CompoundNode(trait=self._trait, payload=None, parent=parent)
        start = offset
        items = {}
        while True:
          item, name, offset = TAG.parse(base, offset, parent=container)
          if type(item) is End:
            break
          container[name] = item
          
        container._payload = base[start:offset]
        return container, offset

# ==================================================================== 
# Traits
# ==================================================================== 
class TraitMetaclass(type):
    TRAITS = {}

    """ A little bit of black magic to tune traits attributes
    """
    def __new__(meta, cls, bases, dct):
        cls = super().__new__(meta, cls, bases, dct)

        # tune READER
        READER = getattr(cls, 'READER', None)
        if READER is not None:
          cls.make_from_payload = READER(cls).make_from_payload

        # collect traits IDs
        ID = dct.get('ID')
        if ID is not None:
          meta.TRAITS[ID] = cls

        return cls

class Trait(metaclass=TraitMetaclass):
    """ Define various properties for individual types
    """
    pass
    
class AtomTrait(Trait):
    READER = AtomReader

class ArrayTrait(Trait):
    READER = ArrayReader

class EndTrait(Trait):
    ID = 0
    # READER = EndReader

class ByteTrait(AtomTrait):
    ID = 1
    SIZE = 1
    FORMAT = ">b"
    VALUE = Integer

class ShortTrait(AtomTrait):
    ID = 2
    SIZE = 2
    FORMAT = ">h"
    VALUE = Integer

class IntTrait(AtomTrait):
    ID = 3
    SIZE = 4
    FORMAT = ">i"
    VALUE = Integer

class LongTrait(AtomTrait):
    ID = 4
    SIZE = 8
    FORMAT = ">q"
    VALUE = Integer

class FloatTrait(AtomTrait):
    ID = 5
    SIZE = 4
    FORMAT = ">f"
    VALUE = Float

class DoubleTrait(AtomTrait):
    ID = 6
    SIZE = 8
    FORMAT = ">d"
    VALUE = Float

class Byte_ArrayTrait(ArrayTrait):
    ID = 7
    SIZE = 1
    FORMAT = ">b"

class Int_ArrayTrait(ArrayTrait):
    ID = 11
    SIZE = 4
    FORMAT = ">i"

class Long_ArrayTrait(ArrayTrait):
    ID = 12
    SIZE = 8
    FORMAT = ">q"
    READER = ArrayReader

class StringTrait(Trait):
    ID = 8
    VALUE = String
    READER = StringReader

class ListTrait(Trait):
    ID = 9
    READER = ListReader

class CompoundTrait(Trait):
    ID = 10
    READER = CompoundReader

TYPE_TO_TRAIT = {
    int:    IntTrait,
    float:  DoubleTrait,
    str:    StringTrait,
    bool:   ByteTrait,
}

class NBTNode:
    def __init__(self, bindata=None):
        self.bindata = bindata

    def __repr__(self):
        return "NBTNode({bindata})".format(bindata=rawbytes(bindata)[:30])

class NBTFile(NBTNode):
    def __init__(self, path):
        self.path = path
        with gzip.open(path,"rb") as f:
            super().__init__(f.read())

class NBT:
    def __init__(self, rawbytes):
        self.rawbytes = rawbytes

