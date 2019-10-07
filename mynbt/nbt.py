import gzip
from struct import unpack_from
from weakref import WeakSet

class TAG:
    datatypes = {}

    def __init__(self, value = None, parent = None):
        self.id = self.__class__.id
        self.name = None
        self._value = value
        self.parents = WeakSet()
        self.register_parent(parent)

    def __repr__(self):
        name = self.name
        attr=[]
        if name is not None:
          attr.append("name="+name)
        if self.cache is not None:
          attr.append("cached")

        return "{tag}({attr})".format(tag=self.__class__.__name__, attr=", ".join(attr))

    def register_parent(self,parent):
        if parent is not None:
          self.parents.add(parent)

    def invalidate(self):
        queue = [self]
        while queue:
          item = queue.pop()
          if item.cache:
            item.cache = None
            queue.extend(item.parents)

    def export(self, compact=True):
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

    def _get_value(self):
        return self.get_value()

    def get_value(self):
        if self._value is None:
          self._value, = self.unpack()

        return self._value

    def set_value(self):
        self.invalidate()

    def del_value(self):
        pass

    def unpack(self):
        pass

    value = property(_get_value, set_value, del_value)

    @staticmethod
    def parse_id(base, offset):
        id, = unpack_from('>B',base, offset)
        return id,offset+1

    @staticmethod
    def parse_name(base, offset):
        l, = unpack_from('>h',base, offset)
        name = base[offset+2:offset+2+l].decode("utf8")
        return name,offset+2+l

    @staticmethod
    def parse_tag(base, offset):
        id,offset = TAG.parse_id(base, offset)
        tag = TAG.datatypes[id]
        assert tag.id == id

        return tag, offset

    @staticmethod
    def parse(base, offset, parent = None):
        start = offset
        tag, offset = TAG.parse_tag(base,offset)
        result = tag(parent=parent)
        if tag is not TAG_End:
          result.name, offset = result.parse_name(base, offset)
          offset = result.parse_payload(base, offset)

        result.cache = base[start:offset]

        return result, offset

    @staticmethod
    def parse_file(path):
        with gzip.open(path, "rb") as f:
          data = f.read()
          result, offset = TAG.parse(data, 0)

        assert data[offset:] == b""
        return result

class TAG_End(TAG):
    id = 0

class TAG_Byte(TAG):
    id = 1

    def parse_payload(self, base, offset):
        return offset+1

class TAG_Short(TAG):
    id = 2

    def parse_payload(self, base, offset):
        return offset+2

    def unpack(self):
        return unpack_from(">h", self.cache[-2:])

class TAG_Int(TAG):
    id = 3

    def parse_payload(self, base, offset):
        return offset+4

class TAG_Long(TAG):
    id = 4

    def parse_payload(self, base, offset):
        return offset+8

class TAG_Float(TAG):
    id = 5

    def parse_payload(self, base, offset):
        return offset+4

class TAG_Double(TAG):
    id = 6

    def parse_payload(self, base, offset):
        return offset+8

class TAG_Byte_Array(TAG):
    id = 7

    def parse_payload(self, base, offset):
        l, = unpack_from('>i',base, offset)
        return offset+4+l*1

class TAG_String(TAG):
    id = 8

    def parse_payload(self, base, offset):
        l, = unpack_from('>h',base, offset)
        return offset+2+l

class TAG_List(TAG):
    id = 9

    def parse_payload(self, base, offset):
        tag, offset = TAG.parse_tag(base, offset)
        count, = unpack_from('>i',base, offset)
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
          offset = item.parse_payload(base, offset)
          items.append(item)
          count -= 1
       
        self.items = items
        return offset

class TAG_Compound(TAG):
    id = 10

    def __init__(self, *args, **kwargs):
        self.items = {}
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return super().__repr__() + " {" +\
                ", ".join(repr(item) for item in self.items) +\
                "}"

    def parse_payload(self, base, offset):
        items = {}
        while True:
          item, offset = TAG.parse(base, offset, parent=self)
          if type(item) is TAG_End:
            break
          items[item.name] = item
          
        self.items = items
        return offset

    def keys(self):
        return self.items.keys()

    def export(self, compact=True):
        """ Export a NBT data structure as Python native objects.
        """
        value = {k: v.export(compact) for k, v in self.items.items()}

        if compact:
          return value
        else:
          return {
            'type': self.__class__.__name__,
            'value': value
          }

    def get_value(self):
        return self.items

    def __getitem__(self, name):
        item = self.items[name]

        return item.value

    def __getattr__(self, name):
        return self[name]

TAG.datatypes = { t.id: t for t in (
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
    TAG_Compound
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

