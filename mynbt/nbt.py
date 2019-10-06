import gzip
from struct import unpack

class TAG:
    datatypes = {}

    def __init__(self):
        self.id = self.__class__.id

    def consume(self, rawbytes):
        id, = unpack('>B',rawbytes[0:1])
        assert id == self.id
        return rawbytes[1:]

    @staticmethod
    def parse(rawbytes):
        tag = TAG.datatypes[rawbytes[0]]
        result = tag()
        result.consume(rawbytes)
        return result

class TAG_Named(TAG):
    def __init__(self):
        super().__init__()

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        l, = unpack('>h',rawbytes[0:2])
        self.name = rawbytes[2:2+l].decode("utf8")
        return rawbytes[2+l:]

class TAG_End(TAG):
    id = 0

class TAG_Byte(TAG_Named):
    id = 1

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        self.payload = rawbytes[0:1]
        return rawbytes[1:]

class TAG_Short(TAG_Named):
    id = 2

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        self.payload = rawbytes[0:2]
        return rawbytes[2:]

class TAG_Int(TAG_Named):
    id = 3

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        self.payload = rawbytes[0:4]
        return rawbytes[4:]

class TAG_Long(TAG_Named):
    id = 4

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        self.payload = rawbytes[0:4]
        return rawbytes[4:]

class TAG_Float(TAG_Named):
    id = 5

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        self.payload = rawbytes[0:4]
        return rawbytes[4:]

class TAG_Double(TAG_Named):
    id = 6

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        self.payload = rawbytes[0:8]
        return rawbytes[8:]

class TAG_Byte_Array(TAG_Named):
    id = 7

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        l, = unpack('>i',rawbytes[0:4])
        self.payload = rawbytes[4:4+l*1]
        return rawbytes[4+l*1:]

class TAG_String(TAG_Named):
    id = 8

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        l, = unpack('>h',rawbytes[0:2])
        self.payload = rawbytes[2:2+l]
        return rawbytes[2+l:]

class TAG_List(TAG_Named):
    id = 9

    def consume(self, rawbytes):
        rawbytes = super().consume(rawbytes)
        item_type = rawbytes[0]
        count, = unpack('>i',rawbytes[1:5])
        # XXX Check implications of that statement:
        # """ If the length of the list is 0 or negative, 
        #     the type may be 0 (TAG_End) but otherwise it must 
        #     be any other type. """
        #  -- https://wiki.vg/NBT#Specification

        if count < 0:
            count = 0
        self.items = [None]*count

        self.payload = rawbytes[2:2+l]
        return rawbytes[2+l:]

TAG.datatypes = { t.id: t for t in (
    TAG_End,
    TAG_Byte,
    TAG_Short,
    TAG_Int,
    TAG_Long,
    TAG_Float,
    TAG_Double,
    TAG_Byte_Array,
    TAG_String
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

