import unittest

from io import BytesIO
from mynbt.region import *
import mynbt.nbt as nbt

class TestRegion(unittest.TestCase):
    def test_1(self):
        """ Region without data should have all chunks empty
        """
        region = Region()
        chunks = [region.chunk_info(x,y) for x in range(32) for y in range(32)]
        self.assertSequenceEqual(chunks, [EmptyChunk]*32*32)

    def test_2(self):
        """ Region with incomplete headers should be silently fixed
        """
        region = Region(b"\x00"*(PAGE_SIZE//2))
        chunks = [region.chunk_info(x,y) for x in range(32) for y in range(32)]
        self.assertSequenceEqual(chunks, [EmptyChunk]*32*32)

    def test_3(self):
        """ Missing data are filled with zero bytes
        """
        addr, size = 5, 3
        broken_header = (5<<8|3)
        region = Region(broken_header.to_bytes(4, 'big'))
        chunk = region.chunk_info(0,0)
        self.assertEqual([chunk.addr,chunk.size], [addr, size])
        self.assertEqual(chunk.data, EmptyPage*size)

    def test_4(self):
        """ Region should compute page usage bitmap
        """
        region = Region.open("test/data/region-r.0.0.mca")
        print(region.bitmap())


    def test_bytes_to_chunk_addr(self):
        addr = bytes_to_chunk_addr(bytes.fromhex("102030405060"), 0)
        self.assertEqual(addr, (0x102030, 0x40))

        addr = bytes_to_chunk_addr(bytes.fromhex("DEADBEEF102030405060"), 4)
        self.assertEqual(addr, (0x102030, 0x40))

    def test_empty_region(self):
        region = Region()
        #self.assertEqual(bytes(region._locations), bytes(4096))
        #self.assertEqual(bytes(region._timestamps), bytes(4096))
        #self.assertEqual(region._eof, 2*4096)

        self.assertEqual(region.chunk_info(1,2), (0, 0, 0, 0, 0, b""))

    def test_set_chunk(self):
        region = Region()
        region.set_chunk(1,2, nbt.Integer(3))
        chunk = region.chunk_info(1,2)
        self.assertEqual((chunk.x,chunk.z), (1, 2))
        self.assertGreater(len(chunk.data), 0)

    def test_region(self):
        region = Region.open("test/data/region-r.0.0.mca")
        info = region.chunk_info(1,2)
        chunk = region.parse_chunk(1,2)
        # print(chunk.Level.Entities.export())
        # print(chunk.Level.export(scope=['xPos', 'zPos']))

    def test_chunk_iterator(self):
        region = Region.open("test/data/region-r.0.0.mca")
        with region.chunk(1,2) as chunk:
          # print(chunk)
          # print(chunk.Level.Entities.export())
          # print(chunk.Level.export(scope=['xPos', 'zPos']))
          pass

    def test_write_chunk(self):
        region = Region()
        region.set_chunk(1,2, nbt.Integer(3))


        stream = BytesIO()
        region.write_to(stream)

        buffer = stream.getbuffer()

        for i in range(1024):
            self.assertEqual(bytes(buffer[i*4:i*4+4]), b"\x00\x00\x02\x01" if i == 2*32+1 else b"\x00\x00\x00\x00",i)

        with open('test/tmp/dump.bin', 'wb') as f:
            f.write(buffer)

        region = Region.open('test/tmp/dump.bin')
        chunk = region.parse_chunk(1,2)
        # print(chunk)
