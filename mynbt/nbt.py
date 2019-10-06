import gzip
from struct import unpack_from

class TAG:
    datatypes = {}

    def __init__(self):
        self.id = self.__class__.id


#    def parse_payload(self, rawbytes):
#        pass

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
          result.payload,offset = result.parse_payload(base, offset)

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

    @staticmethod
    def parse_payload(base, offset):
        return base[offset:offset+1], offset+1

class TAG_Short(TAG):
    id = 2

    @staticmethod
    def parse_payload(base, offset):
        return base[offset:offset+2], offset+2

class TAG_Int(TAG):
    id = 3

    @staticmethod
    def parse_payload(base, offset):
        return base[offset:offset+4], offset+4

class TAG_Long(TAG):
    id = 4

    @staticmethod
    def parse_payload(base, offset):
        return base[offset:offset+8], offset+8

class TAG_Float(TAG):
    id = 5

    @staticmethod
    def parse_payload(base, offset):
        return base[offset:offset+4], offset+4

class TAG_Double(TAG):
    id = 6

    @staticmethod
    def parse_payload(base, offset):
        return base[offset:offset+8], offset+8

class TAG_Byte_Array(TAG):
    id = 7

    @staticmethod
    def parse_payload(base, offset):
        l, = unpack_from('>i',base, offset)
        return base[offset+4:offset+4+l*1], offset+4+l*1

class TAG_String(TAG):
    id = 8

    @staticmethod
    def parse_payload(base, offset):
        l, = unpack_from('>h',base, offset)
        return base[offset+2:offset+2+l], offset+2+l

class TAG_List(TAG):
    id = 9

    @staticmethod
    def parse_payload(base, offset):
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
          item.payload,offset = item.parse_payload(base, offset)
          items.append(item)
          count -= 1
        
        return items,offset

class TAG_Compound(TAG):
    id = 10

    def __repr__(self):
        return "TAG_Compound(" +\
                ", ".join(repr(item) for item in items) +\
                ")"

    @staticmethod
    def parse_payload(base, offset):
        items = []
        while True:
          item, offset = TAG.parse(base, offset)
          if type(item) is TAG_End:
            break
          items.append(item)
          
        return items,offset

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

