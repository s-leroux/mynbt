import gzip
from struct import unpack

class TAG:
    datatypes = {}

    def __init__(self):
        self.id = self.__class__.id


#    def parse_payload(self, rawbytes):
#        pass

    @staticmethod
    def parse_id(rawbytes):
        id, = unpack('>B',rawbytes[0:1])
        return id,rawbytes[1:]

    @staticmethod
    def parse_name(rawbytes):
        l, = unpack('>h',rawbytes[0:2])
        name = rawbytes[2:2+l].decode("utf8")
        return name,rawbytes[2+l:]

    @staticmethod
    def parse_tag(rawbytes):
        id,rawbytes = TAG.parse_id(rawbytes)
        tag = TAG.datatypes[id]
        assert tag.id == id

        return tag, rawbytes

    @staticmethod
    def parse(rawbytes):
        tag, rawbytes = TAG.parse_tag(rawbytes)
        result = tag()
        if tag is not TAG_End:
          result.name, rawbytes = result.parse_name(rawbytes)
          result.payload,rawbytes = result.parse_payload(rawbytes)

        return result, rawbytes

    @staticmethod
    def parse_file(path):
        with gzip.open(path, "rb") as f:
          result, garbage = TAG.parse(f.read())

        assert garbage == b""
        return result

class TAG_End(TAG):
    id = 0

class TAG_Byte(TAG):
    id = 1

    @staticmethod
    def parse_payload(rawbytes):
        return rawbytes[0:1], rawbytes[1:]

class TAG_Short(TAG):
    id = 2

    @staticmethod
    def parse_payload(rawbytes):
        return rawbytes[0:2], rawbytes[2:]

class TAG_Int(TAG):
    id = 3

    @staticmethod
    def parse_payload(rawbytes):
        return rawbytes[0:4], rawbytes[4:]

class TAG_Long(TAG):
    id = 4

    @staticmethod
    def parse_payload(rawbytes):
        return rawbytes[0:8], rawbytes[8:]

class TAG_Float(TAG):
    id = 5

    @staticmethod
    def parse_payload(rawbytes):
        return rawbytes[0:4], rawbytes[4:]

class TAG_Double(TAG):
    id = 6

    @staticmethod
    def parse_payload(rawbytes):
        return rawbytes[0:8], rawbytes[8:]

class TAG_Byte_Array(TAG):
    id = 7

    @staticmethod
    def parse_payload(rawbytes):
        l, = unpack('>i',rawbytes[0:4])
        return rawbytes[4:4+l*1], rawbytes[4+l*1:]

class TAG_String(TAG):
    id = 8

    @staticmethod
    def parse_payload(rawbytes):
        l, = unpack('>h',rawbytes[0:2])
        return rawbytes[2:2+l], rawbytes[2+l:]

class TAG_List(TAG):
    id = 9

    @staticmethod
    def parse_payload(rawbytes):
        tag, rawbytes = TAG.parse_tag(rawbytes)
        count, = unpack('>i',rawbytes[0:4])
        rawbytes = rawbytes[4:]
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
          item.payload,rawbytes = item.parse_payload(rawbytes)
          items.append(item)
          count -= 1
        
        return items,rawbytes

class TAG_Compound(TAG):
    id = 10

    def __repr__(self):
        return "TAG_Compound(" +\
                ", ".join(repr(item) for item in items) +\
                ")"

    @staticmethod
    def parse_payload(rawbytes):
        items = []
        while True:
          item, rawbytes = TAG.parse(rawbytes)
          if type(item) is TAG_End:
            break
          items.append(item)
          
        return items,rawbytes

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

