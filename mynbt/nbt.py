import gzip
import struct
from weakref import WeakSet
import collections
from collections.abc import Hashable, MutableSequence
from array import array

import io

from mynbt.visitor import Visitor, Exporter
from mynbt.error import *
from mynbt.utils import patch,withsave
import mynbt.bitpack as bitpack

# ====================================================================
# Errors
# ====================================================================
class NBTError(MyNBTError):
    pass

class EmptyChunkError(NBTError):
    def __init__(self, region, x, y):
        super().__init__("The chunk ({x},{y}) of region {region} is empty", x=x,y=y,region=region)

class CircularReferenceError(NBTError):
    def __init__(self):
        super().__init__("Circular reference detected")

# ====================================================================
# Module functions
# ====================================================================
def parse_id(base, offset):
    ID, = struct.unpack('>B',bytes(base[offset:offset+1]))
    return ID,offset+1

def parse_name(base, offset):
    l, = struct.unpack('>h',bytes(base[offset:offset+2]))
    name = bytes(base[offset+2:offset+2+l]).decode("utf8")
    return name,offset+2+l

def parse_tag(base, offset):
    ID,offset = parse_id(base, offset)
    trait = TraitMetaclass.TRAITS[ID]
    assert trait.ID == ID

    return trait, offset

def parse(base, offset=0, parent=None):
    base = memoryview(base)
    start = offset
    name = None
    trait, offset = parse_tag(base,offset)
    if trait is EndTrait:
      result = End(parent=parent)
    else:
      name, offset = parse_name(base, offset)
      result, offset = trait.make_from_payload(base, offset, parent=parent)

    return result, name, offset

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

    result, name, offset = parse(data, 0)
    assert data[offset:] == b""

    #
    # monkey patch the root object to add a save() method
    # In addition, the object behaves as a context manager
    # to save the file on exit
    old_version = result._version
    patch(result, withsave(path, reader, lambda : result._version > old_version))

    return result

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
        self._version = 0
        self._trait = trait
        self._payload = payload
        self._parents = WeakSet()
        if parent is not None:
            self.register_parent(parent)

    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, value, *, parent=None):
        """ The base implementation try to be smart and will
            delegate to the right subclass
        """
        if isinstance(value, Node):
            return value # XXX Shouldn't we clone here?

        MAP = {
          int: Integer,
          float: Float,
          array: Array,
          dict: CompoundNode,
          str: String,
        }

        cls = MAP.get(type(value))
        if cls is None:
            # fallback to linear search in case of
            # derived classes
            for t, cls in MAP.items():
                if isinstance(value, t):
                    break
            else:
                # If all else has failed, it may still be a sequence
                try:
                    value = tuple(value)
                except:
                    raise TypeError("Cannot identify the right node type for {} ({})".format(value, type(value)))

                # sequences may either be Array or List
                try:
                    nbits = max(n.bit_length() for n in value)
                except AttributeError:
                    cls = ListNode
                else:
                    for n,t in ((8, 'b'), (32, 'i'), (64, 'q')):
                        if nbits <= n:
                            return Array.fromNativeObject(value, typecode=t, parent=parent)
                    else:
                        raise ValueError("Cannot represent {} bits values".format(nbits))


        return cls.fromNativeObject(value, parent=parent)

    def clone(self, parent=None):
        """ Clone the receiver.
            Immutle values should return self
        """
        if parent:
            self.register_parent(parent)

        return self

    #------------------------------------
    # Managing ancestors chain
    #------------------------------------
    def register_parent(self,parent):
        assert isinstance(parent, Node), "Parent must be  valid NBT node " + str(type(parent))
        # Only composite nodes can induce circular references
        # if parent.has_ancestor(self):
        #     raise "Circular reference detected"

        self._parents.add(parent)

    def register_parents(self,parents):
        for parent in parents:
            self.register_parent(parent)
        return self

    G_VERSION=0
    def invalidate(self):
        Node.G_VERSION+=1
        version = Node.G_VERSION

        queue = [self]
        while queue:
          item = queue.pop()
          if item._version < version:
            item._version = version
            item._payload = None
            queue.extend(item._parents)
          else:
            assert item._payload is None

    def has_ancestor(self, target):
        """ Check if a node is self's ancestors list.
            Used mostly for cycle detection.
        """
        queue = [self]
        while queue:
          item = queue.pop()
          if target is item:
            return True

          queue.extend(item._parents)

        return False

    #------------------------------------
    # NBT tree traversal
    #------------------------------------
    def children(self):
        """ Yield a (name, node) tupple for each child of
            the node.

            Subclasses should ensure children are returned in a deterministic order
        """
        yield from ()

    def visit(self, visitor=Visitor(), *, rootname="", filter=lambda path, name, node: True):
        """ Iterate over the NBT tree in depth-first order, calling
            the visitor's methods when entering and leaving the node

            The filter parameter controls if the subtree at path
            should be explored
        """
        def curry(f, *args):
            return lambda : f(*args)

        def enter(path, name, node):
            stack.append(curry(leave, path, name, node))
            if filter(path, name, node):
                for childname, childnode in reversed(list(node.children())):
                    stack.append(curry(enter, path + "." + str(childname), childname, childnode))

            return visitor.enter(path, name, node)

        def leave(path, name, node):
            return visitor.leave(path, name, node)

        def close():
            return visitor.close()

        stack = [close, curry(enter, rootname, rootname, self)]
        while stack:
            action = stack.pop()
            result = action()
            if result is not None:
                yield result

    def walk(self, *, rootname="", filter=lambda path, name, node: True):
        """ Iterate over the NBT tree yielding (path, name, node) tupple
            for each item.

            The filter parameter controls if the subtree at path
            should be explored
        """
        class V(Visitor):
            def enter(self, path, name, node):
                return (path, name, node)

        return self.visit(V(), rootname=rootname,filter=filter)

    #------------------------------------
    # Exporting NBT values
    #------------------------------------
    def write_to(self, output, name=""):
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
        self.write_to(output, name)
        return output.getbuffer()

    def write_payload(self, output):
        if self._payload is None:
            raise ValueError

        output.write(self._payload)

    def export(self, *, compact=True):
        if not compact:
            raise NotImplementedError
        result, = self.visit(Exporter())
        return result

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
        return struct.pack(self._trait.FORMAT, self)

class Integer(int, Value):
    def __new__(cls, value, **kwargs):
        return int.__new__(cls, value)

    def __init__(self, value, *, trait = None, payload = None, parent = None):
        Node.__init__(self, trait = trait or IntTrait, payload = payload, parent = parent)

    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, value, *, typecode='>h', parent=None):
        value = int(value)

        TYPECODES = { trait.FORMAT[-1] : trait for trait in (
            ByteTrait,
            ShortTrait,
            IntTrait,
            LongTrait
        ) }

        try:
            trait = TYPECODES[typecode[-1]]
        except KeyError:
            raise ValueError("Typecode should be one of {}, not {}".format(tuple(TYPECODES.keys()), typecode[-1]))

        return cls(value, trait=trait, parent=parent)

class Float(float, Value):
    def __new__(cls, value, **kwargs):
        return float.__new__(cls, value)

    def __init__(self, value, *, trait = None, payload = None, parent = None):
        Node.__init__(self, trait = trait or DoubleTrait, payload = payload, parent = parent)

    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, value, *, typecode='>d', parent=None):
        value = float(value)

        TYPECODES = { trait.FORMAT[-1] : trait for trait in (
            FloatTrait,
            DoubleTrait,
        ) }

        try:
            trait = TYPECODES[typecode[-1]]
        except KeyError:
            raise ValueError("Typecode should be one of {}, not {}".format(tuple(TYPECODES.keys()), typecode[-1]))

        return cls(value, trait=trait, parent=parent)

class String(str, Value):
    def __new__(cls, value, **kwargs):
        return str.__new__(cls, value)

    def __init__(self, value, *, trait = None, payload = None, parent = None):
        Node.__init__(self, trait = trait or StringTrait, payload = payload, parent = parent)

    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, obj, *, parent=None):
        return cls(str(obj), parent=parent)

    def pack(self):
        data = self.encode('utf8')

        return len(data).to_bytes(2, 'big') + data

# ====================================================================
# Arrays
# ====================================================================
class Array(Value):
    """ An array of integral (byte, int, long) types.

        Array are backed by python's `array.array` objects. They can be reshaped
        without invalidating the node since the byte-level data remain inchanged.
    """
    def __init__(self, *, trait, payload = None, parent = None):
        Value.__init__(self, trait = trait, payload = payload, parent = parent)
        self._array = array(trait.FORMAT[-1]) # skip endianness

        nbits = self._array.itemsize*8
        self._nbits_f = nbits if callable(nbits) else lambda: nbits


    @classmethod
    def fromValues(cls, values, *, trait, payload = None, parent = None):
        instance = cls(trait=trait, payload=payload, parent=parent)
        instance._array.extend(values)
        return instance

    @property
    def typecode(self):
        return self._array.typecode

    def reshape(self, dst_nbits):
        """ Reshape the array so each sequence of nbits becomes an items
        """
        dst_nbits_f = dst_nbits if callable(dst_nbits) else lambda: dst_nbits
        self._array = bitpack.unpack(dst_nbits_f(), self._nbits_f(), self._array)
        self._nbits_f = dst_nbits_f


    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, sequence, *, typecode=None, parent=None):
        try:
            typecode = sequence.typecode
        except AttributeError:
            if typecode is None:
                raise ValueError("typecode must be set if the sequence doesn't provide it")

        TYPECODES = { trait.FORMAT[-1] : trait for trait in (
            ByteArrayTrait,
            IntArrayTrait,
            LongArrayTrait
        ) }

        try:
            trait = TYPECODES[typecode[-1]]
        except KeyError:
            raise ValueError("Typecode should be one of {}, not {}".format(tuple(TYPECODES.keys()), typecode[-1]))

        instance = cls(trait=trait, parent=parent)
        instance._array.extend(sequence)

        return instance

    #------------------------------------
    # Node interface
    #------------------------------------
    def clone(self, parent=None):
        instance = self.__class__(trait=self._trait, payload=self._payload, parent=parent)
        instance.extend(self._array)

        return instance

    def children(self):
        return enumerate(Integer(v, trait=self._trait.TYPE, parent=self) for v in self._array)

    def write_payload(self, output):
        data = self._array
        nbits = self._nbits_f()
        expected_nbits = 8*self._trait.SIZE

        if nbits != expected_nbits:
            data = bitpack.unpack(expected_nbits, nbits, data)

        self._write_payload(self._trait.SIZE, data, output)

    @staticmethod
    def _write_payload(size, data, output):
        count = len(data)
        output.write(count.to_bytes(4, 'big'))
        # hack
        typecode = bitpack.UINT_SIZE[size]
        view = memoryview(data).cast(bitpack.UINT_8).cast(typecode)
        SEGSIZE=min(1024, count) # actually SEGSIZE is the sive in items, not bytes
        buffer=bytearray(SEGSIZE*size)
        fmt = ">" + typecode*SEGSIZE
        while len(view) > SEGSIZE:
            head = view[:SEGSIZE]
            view = view[SEGSIZE:]

            struct.pack_into(fmt, buffer, 0, *head)
            output.write(buffer)

        remaining = len(view)

        if remaining:
            fmt = fmt[:remaining+1]
            buffer = memoryview(buffer)[:remaining*size]
            struct.pack_into(fmt, buffer, 0, *view)
            output.write(buffer)

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

    def __setitem__(self, idx, value):
        self.invalidate()
        self._array.__setitem__(idx, value)

    def __getitem__(self, idx):
        return self._array.__getitem__(idx)

    # def __delitem__(self, idx):
    #     self.invalidate()
    #     # using a WeakKeyDictionary we may emulate multibag and remove self
    #     # from the removed item parent list
    #     del self._items[idx]

    def insert(self, idx, value):
        self.invalidate()
        self._array.insert(idx, value)

    #------------------------------------
    # Sequence interface
    #------------------------------------
    def __iter__(self):
        return self._array.__iter__()

    def __len__(self):
        return self._array.__len__()

# ====================================================================
# Proxy
# ====================================================================
class Proxy(Node):
    """ A proxy stores binary NBT data as read from a binary stream
        (i.e. without decoding them)

        This avoid spending time decoding uneeded data. It also
        speed-up writing back unmodified data
    """
    def __init__(self, *, trait, payload=None, parent = None):
        super().__init__(trait=trait, payload=payload, parent=parent)
        self._value = None

    def __repr__(self):
        return repr("{base}[{trait},{payload}]".format(base=super().__repr__(), trait=self._trait, payload=self._payload))

    def __str__(self):
        return self.value().__str__()

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
        if self._value is None:
            self._value = self._trait.instanceFromValue(self.unpack(), payload=self._payload)

        return self._value

    def write_payload(self, output):
        output.write(self._payload)

class AtomProxy(Proxy):
    def unpack(self):
        return struct.unpack(self._trait.FORMAT, self._payload)[0]

class ArrayProxy(Proxy):
    def unpack(self):
        return (v for v, in struct.iter_unpack(self._trait.FORMAT, self._payload[4:]))

    #------------------------------------
    # Node interface
    #------------------------------------
    def children(self):
        return self.value().children()

    def __iter__(self):
        return self.value().__iter__()

class StringProxy(Proxy):
    def unpack(self):
        return bytes(self._payload[2:]).decode("utf8") # XXX unneeded (?) copy

# ====================================================================
# Composites
# ====================================================================
class Composite(Node):
    KeyOrIndexError = KeyError

    #------------------------------------
    # Managing ancestors chain
    #------------------------------------
    def register_parent(self,parent):
        # Only composite nodes can induce circular references
        if parent.has_ancestor(self):
            raise CircularReferenceError()

        super().register_parent(parent)

    #------------------------------------
    # Mutable sequence interface
    #------------------------------------
    def __getitem__(self, idx):
        sentinelle = object()

        node = self._get(idx, sentinelle)
        if node is sentinelle:
            raise self.KeyOrIndexError(idx)

        value = node.value()

        if value is not node:
            value.register_parent(self)
            super(Node, self).__setitem__(idx, value)

        return value

    @staticmethod
    def withInvalidate(method):
        def f(self, *args, **kwargs):
            self.invalidate()
            return method(self, *args, **kwargs)
        return f

class ListNode(Composite, list, collections.abc.Hashable):
    KeyOrIndexError = IndexError

    def __init__(self, *, trait=None, child_trait, payload=None, parent=None):
        self._child_trait = child_trait
        super().__init__(trait=trait or ListTrait, payload=payload, parent=parent)
        list.__init__(self)

    def __str__(self):
        return str(self.export())

    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, sequence, *, parent=None, child_trait=None):
        identity = lambda x : x

        if not child_trait:
            rules = [
              (ByteTrait, lambda x : isinstance(x, int) and -(1<<7) <= x <= (1<<7)-1 , identity),
              (IntTrait, lambda x : isinstance(x, int) and -(1<<31) <= x <= (1<<31)-1 , identity),
              (LongTrait, lambda x : isinstance(x, int) and -(1<<63) <= x <= (1<<63)-1 , identity),
              (FloatTrait, lambda x : isinstance(x, float), identity),
              (StringTrait, lambda x : isinstance(x, str), identity),
              (CompoundTrait, lambda x : isinstance(x, dict), identity),
              (FloatTrait, lambda x : float(x) == x, float),
              (StringTrait, lambda x : True, str),
            ]
            guess = { idx: [] for idx, rule in enumerate(rules) }

            for item in sequence:
                kill = []
                for idx, l in guess.items():
                    try:
                        if rules[idx][1](item):
                            l.append(rules[idx][2](item))
                            continue
                    except:
                        pass
                    kill.append(idx)

                for k in kill:
                    del guess[k]

            for idx, (child_trait, *_) in enumerate(rules):
                sequence = guess.get(idx)
                if sequence is not None:
                    break

        if not child_trait:
            raise TypeError("Can't guess the proper list type")

        instance = cls(child_trait=child_trait,parent=parent)
        instance.extend((child_trait.instanceFromValue(item, parent=instance) for item in sequence))

        return instance

    #------------------------------------
    # Node interface
    #------------------------------------
    def clone(self, parent=None):
        instance = self.__class__(trait=self._trait, child_trait=self._child_trait, payload=self._payload, parent=parent)
        instance.extend(item.clone(parent=instance) for item in self)

        return instance

    def children(self):
        return enumerate(self)

    def write_payload(self, output):
        output.write((self._child_trait.ID).to_bytes(1, 'big'))
        output.write(len(self).to_bytes(4, 'big'))
        for item in self:
            item.write_payload(output)

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
    def _get(self, idx, default=None):
        try:
            return list.__getitem__(self, int(idx))
        except:
            return default

    def __setitem__(self, idx, value):
        idx = int(idx)
        if not isinstance(value, Node):
            value = self._child_trait.instanceFromValue(value)

        self.invalidate()
        value.register_parent(self)
        list.__setitem__(self, idx, value)

    def __delitem__(self, idx):
        idx = int(idx)
        self.invalidate()
        # using a WeakKeyDictionary we may emulate multibag and remove self
        # from the removed item parent list
        list.__delitem__(self, idx)

    def insert(self, i, value):
        if not isinstance(value, Node):
            value = self._child_trait.instanceFromValue(value)
        value.register_parent(self)
        self.invalidate()

        super().insert(i, value)

    def append(self, value):
        if not isinstance(value, Node):
            value = self._child_trait.instanceFromValue(value)
        value.register_parent(self)
        self.invalidate()

        super().append(value)

    def extend(self, iterable):
        self.invalidate()
        super().extend(self._child_trait.instanceFromValue(value, parent=self) if not isinstance(value, Node) else value for value in iterable)


class CompoundNode(Composite, dict, collections.abc.Hashable):
    def __init__(self, *, trait=None, payload=None, parent=None):
        if trait is None:
            trait = CompoundTrait

        super().__init__(trait=trait, payload=payload, parent=parent)
        dict.__init__(self)

    # override mutable methods
    for m in (): # XXX To be defined
        vars()[m] = Composite.withInvalidate(getattr(dict, m))

    def __repr__(self):
        return super().__repr__() + " {" +\
                ", ".join(name + ": " + repr(item) for name, item in self.items()) +\
                "}"

    def __str__(self):
        return str(self.export())

    #------------------------------------
    # Converion from native objects
    #------------------------------------
    @classmethod
    def fromNativeObject(cls, dict_like_object, *, trait = None, parent=None):
        instance = cls(parent=parent, trait = trait or cls)
        instance.update({k:Node.fromNativeObject(v, parent=instance) for k,v in dict_like_object.items()})

        return instance


    #------------------------------------
    # Node interface
    #------------------------------------
    def clone(self, parent=None):
        instance = self.__class__(trait=self._trait, payload=self._payload, parent=parent)
        instance.update({k:v.clone(parent=instance) for k,v in self.items()})

        return instance

    def children(self):
        return sorted(self.items())

    def write_payload(self, output):
        for name, item in self.items():
            item.write_to(output, name=name)
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
    def _get(self, idx, default=None):
        return dict.get(self, str(idx), default)

    def get(self, idx, default=None):
        try:
            return self.__getitem__(str(idx))
        except KeyError:
            return default

    def __setitem__(self, idx, value):
        idx = str(idx)
        self.invalidate()
        if not isinstance(value, Node):
            # Non-Node objects must be promoted.
            # if the new value replace an existing one, the value keep the same type
            # otherwise a compatible type is inferred
            old = self.get(idx)
            if old:
                value = old._trait.instanceFromValue(value)
            else:
                value = Node.fromNativeObject(value)

        value.register_parent(self)
        dict.__setitem__(self, idx, value)

        return value

    def __delitem__(self, idx):
        self.invalidate()
        dict.__delitem__(self, idx)

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
        l, = struct.unpack('>i',bytes(base[offset:offset+4]))
        payload = base[offset:offset+4+l*self._trait.SIZE]
        return ArrayProxy(trait=self._trait, payload=payload, parent=parent),offset+4+l*self._trait.SIZE

class StringReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        l, = struct.unpack('>h',bytes(base[offset:offset+2]))
        payload = base[offset:offset+2+l]
        return StringProxy(trait=self._trait, payload=payload, parent=parent),offset+2+l

class ListReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        start = offset

        child_trait, offset = parse_tag(base, offset)
        count, = struct.unpack('>i',bytes(base[offset:offset+4]))
        offset += 4
        # XXX Check implications of that statement:
        # """ If the length of the list is 0 or negative,
        #     the type may be 0 (End) but otherwise it must
        #     be any other type. """
        #  -- https://wiki.vg/NBT#Specification

        if count < 0:
            count = 0

        container = ListNode(trait=self._trait, child_trait=child_trait, payload=None, parent=parent)

        items = []
        while count > 0:
          item, offset = child_trait.make_from_payload(base, offset, parent=container)
          list.append(container, item) # direct access to the storage to bypass invalidate()

          count -= 1

        container._payload = base[start:offset]
        return container, offset

class CompoundReader(Reader):
    def make_from_payload(self, base, offset, *, parent):
        container = CompoundNode(trait=self._trait, payload=None, parent=parent)
        start = offset
        items = {}
        while True:
          item, name, offset = parse(base, offset, parent=container)
          if type(item) is End:
            break
          dict.__setitem__(container, name, item) # direct access to the storage to bypass invalidate()

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
          assert ID not in meta.TRAITS, "duplicate ID for " + cls.__class__.__name__ + " and " + meta.TRAITS[ID].__class__.__name__
          meta.TRAITS[ID] = cls

        return cls

class Trait(metaclass=TraitMetaclass):
    """ Define various properties for individual types
    """
    @classmethod
    def accept(cls, visitor):
        """ Call the most specialized visitor method for this node
        """
        return visitor.__getattribute__(cls.VISIT)();

    @classmethod
    def instanceFromValue(cls, *args, **kwargs):
        try:
            return cls.FACTORY(*args, trait=cls, **kwargs)
        except:
            import pdb; pdb.set_trace()

class NoTrait(Trait):
    pass

class AtomTrait(Trait):
    READER = AtomReader
    VISIT = 'visitAtom'

class ArrayTrait(Trait):
    READER = ArrayReader
    VISIT = 'visitArray'
    FACTORY = Array.fromValues

class EndTrait(Trait):
    ID = 0
    # READER = EndReader
    VISIT = 'visitEnd'

class ByteTrait(AtomTrait):
    ID = 1
    SIZE = 1
    FORMAT = ">" + bitpack.INT_8
    FACTORY = Integer
    VISIT = 'visitByte'

class ShortTrait(AtomTrait):
    ID = 2
    SIZE = 2
    FORMAT = ">" + bitpack.INT_16
    FACTORY = Integer
    VISIT = 'visitShort'

class IntTrait(AtomTrait):
    ID = 3
    SIZE = 4
    FORMAT = ">" + bitpack.INT_32
    FACTORY = Integer
    VISIT = 'visitInt'

class LongTrait(AtomTrait):
    ID = 4
    SIZE = 8
    FORMAT = ">" + bitpack.INT_64
    FACTORY = Integer
    VISIT = 'visitLong'

class FloatTrait(AtomTrait):
    ID = 5
    SIZE = 4
    FORMAT = ">f"
    FACTORY = Float
    VISIT = 'visitFloat'

class DoubleTrait(AtomTrait):
    ID = 6
    SIZE = 8
    FORMAT = ">d"
    FACTORY = Float
    VISIT = 'visitDouble'

class ByteArrayTrait(ArrayTrait):
    ID = 7
    SIZE = 1
    FORMAT = ">" + bitpack.INT_8
    TYPE = ByteTrait
    VISIT = 'visitByteArray'

class IntArrayTrait(ArrayTrait):
    ID = 11
    SIZE = 4
    FORMAT = ">" + bitpack.INT_32
    TYPE = IntTrait
    VISIT = 'visitIntArray'

class LongArrayTrait(ArrayTrait):
    ID = 12
    SIZE = 8
    FORMAT = ">" + bitpack.INT_64
    TYPE = LongTrait
    VISIT = 'visitLongArray'

class StringTrait(Trait):
    ID = 8
    FACTORY = String
    READER = StringReader
    VISIT = 'visitString'

class ListTrait(Trait):
    ID = 9
    READER = ListReader
    VISIT = 'visitList'
    FACTORY = ListNode.fromNativeObject

class CompoundTrait(Trait):
    ID = 10
    READER = CompoundReader
    VISIT = 'visitCompound'
    FACTORY = CompoundNode.fromNativeObject

TYPE_TO_TRAIT = {
    int:    IntTrait,
    float:  DoubleTrait,
    str:    StringTrait,
    bool:   ByteTrait,
}

