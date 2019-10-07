import gzip
from struct import unpack_from

class TAG:
    datatypes = {}

    def __init__(self, value = None):
        self.id = self.__class__.id
        self._value = value

    def _get_value(self):
        return self.get_value()

    def get_value(self):
        if self._value is None:
          self._value, = self.unpack()

        return self._value

    def set_value(self):
        pass

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
    def parse(base, offset):
        start = offset
        tag, offset = TAG.parse_tag(base,offset)
        result = tag()
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
          item = tag()
          offset = item.parse_payload(base, offset)
          items.append(item)
          count -= 1
       
        self.items = items
        return offset

class TAG_Compound(TAG):
    id = 10

    def __repr__(self):
        return "TAG_Compound(" +\
                ", ".join(repr(item) for item in items) +\
                ")"

    def parse_payload(self, base, offset):
        items = {}
        while True:
          item, offset = TAG.parse(base, offset)
          if type(item) is TAG_End:
            break
          items[item.name] = item
          
        self.items = items
        return offset

    def keys(self):
        return self.items.keys()

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

