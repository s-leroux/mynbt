import gzip
from struct import unpack, iter_unpack
from weakref import WeakSet
import collections
from .utils import rslice

class TAG:
    datatypes = {}

    def __init__(self, value = None, parent = None):
        self._id = self.__class__.ID
        self._value = value
        self._parents = WeakSet()
        self.register_parent(parent)

    def __repr__(self):
        attr=[]
        if self._payload is not None:
          attr.append("cached")

        return "{tag}({attr})".format(tag=self.__class__.__name__, attr=", ".join(attr))

    def register_parent(self,parent):
        if parent is not None:
          self._parents.add(parent)

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
        tag = TAG.datatypes[ID]
        assert tag.ID == ID

        return tag, offset

    @staticmethod
    def parse(base, offset, parent = None):
        base = rslice(base)
        start = offset
        name = None
        tag, offset = TAG.parse_tag(base,offset)
        result = tag(parent=parent)
        if tag is not TAG_End:
          name, offset = result.parse_name(base, offset)
          result._payload, offset = result.parse_payload(base, offset)

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

class TAG_End(TAG):
    ID = 0

class Atom:
    def __repr__(self):
        return super().__repr__() + " " + str(self.value)

    def parse_payload(self, base, offset):
        return base[offset:offset+self.SIZE], offset+self.SIZE

    def unpack(self):
        return unpack(self.FORMAT, bytes(self._payload))[0]

class Array:
    def __repr__(self):
        return super().__repr__() + " " + repr(self.value)

    def parse_payload(self, base, offset):
        l, = unpack('>i',bytes(base[offset:offset+4]))
        return base[offset:offset+4+l*self.SIZE], offset+4+l*self.SIZE

    def unpack(self):
        return list(iter_unpack(self.FORMAT, bytes(self._payload[4:])))

class TAG_Byte(Atom, TAG):
    ID = 1
    SIZE = 1
    FORMAT = ">b"

    #def parse_payload(self, base, offset):
    #    return base[offset:offset+1], offset+1
    #
    #def unpack(self):
    #    return unpack(">b", bytes(self._payload))

class TAG_Short(Atom, TAG):
    ID = 2
    SIZE = 2
    FORMAT = ">h"

class TAG_Int(Atom, TAG):
    ID = 3
    SIZE = 4
    FORMAT = ">i"

class TAG_Long(Atom, TAG):
    ID = 4
    SIZE = 8
    FORMAT = ">q"

class TAG_Float(Atom, TAG):
    ID = 5
    SIZE = 4
    FORMAT = ">f"

class TAG_Double(Atom, TAG):
    ID = 6
    SIZE = 8
    FORMAT = ">d"

class TAG_Byte_Array(Array, TAG):
    ID = 7
    SIZE = 1
    FORMAT = ">b"

class TAG_Int_Array(Array, TAG):
    ID = 11
    SIZE = 4
    FORMAT = ">i"

class TAG_Long_Array(Array, TAG):
    ID = 12
    SIZE = 8
    FORMAT = ">q"

class TAG_String(TAG):
    ID = 8

    def parse_payload(self, base, offset):
        l, = unpack('>h',bytes(base[offset:offset+2]))
        return base[offset:offset+2+l], offset+2+l

    def unpack(self):
        return bytes(self._payload[2:]).decode("utf8")

class TAG_List(TAG, collections.abc.MutableSequence, collections.abc.Hashable):
    ID = 9

    def __init__(self, *args, **kwargs):
        self._items = []
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return super().__repr__() + " {" +\
                ", ".join(repr(item) for item in self._items) +\
                "}"

    def parse_payload(self, base, offset):
        start = offset
        tag, offset = TAG.parse_tag(base, offset)
        count, = unpack('>i',bytes(base[offset:offset+4]))
        offset += 4
        # XXX Check implications of that statement:
        # """ If the length of the list is 0 or negative, 
        #     the type may be 0 (TAG_End) but otherwise it must 
        #     be any other type. """
        #  -- https://wiki.vg/NBT#Specification

        if count < 0:
            count = 0
        items = []
        while count > 0:
          item = tag(parent=self)
          item._payload, offset = item.parse_payload(base, offset)
          items.append(item)
          count -= 1
       
        self._items = items
        return base[start:offset], offset

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

    def get_value(self):
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
        item = self._items[idx]

        return item

    def __setitem__(self, idx, value):
        self.invalidate()
        self._items[idx] = value # XXX should promote native values to TAG_... ?

    def __delitem__(self, idx):
        self.invalidate()
        del self._items[idx]

    def __len__(self):
        return len(self._items)

    def insert(self, idx, value):
        self.invalidate()
        self._items.insert(idx, value)

class TAG_Compound(TAG, collections.abc.MutableMapping, collections.abc.Hashable):
    ID = 10

    def __init__(self, *args, **kwargs):
        self._items = {}
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return super().__repr__() + " {" +\
                ", ".join(name + ": " + repr(item) for name, item in self._items.items()) +\
                "}"

    def parse_payload(self, base, offset):
        start = offset
        items = {}
        while True:
          item, name, offset = TAG.parse(base, offset, parent=self)
          if type(item) is TAG_End:
            break
          items[name] = item
          
        self._items = items
        return base[start:offset], offset

    def keys(self):
        return self._items.keys()

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

    def get_value(self):
        return self

    #------------------------------------
    # Hashable interface
    #------------------------------------
    def __hash__(self):
        return id(self)

    #------------------------------------
    # Mutable mapping interface
    #------------------------------------
    def __getitem__(self, idx):
        item = self._items[idx]

        return item

    def __setitem__(self, idx, value):
        self.invalidate()
        self._items[idx] = value # XXX should promote native values to TAG_... ?

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

TAG.datatypes = { t.ID: t for t in (
    TAG_End,
    TAG_Byte,
    TAG_Short,
    TAG_Int,
    TAG_Long,
    TAG_Float,
    TAG_Double,
    TAG_Byte_Array,
    TAG_String,
    TAG_List,
    TAG_Compound,
    TAG_Int_Array,
    TAG_Long_Array,
        )}

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

