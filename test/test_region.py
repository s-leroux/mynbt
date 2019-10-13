import unittest

from mynbt.region import *
import mynbt.nbt as nbt

class TestRegion(unittest.TestCase):
    def test_bytes_to_chunk_addr(self):
        addr = bytes_to_chunk_addr(bytes.fromhex("102030405060"), 0)
        self.assertEqual(addr, (0x102030, 0x40))

        addr = bytes_to_chunk_addr(bytes.fromhex("DEADBEEF102030405060"), 4)
        self.assertEqual(addr, (0x102030, 0x40))

    def test_empty_region(self):
        region = Region()
        self.assertEqual(bytes(region._locations), bytes(4096))
        self.assertEqual(bytes(region._timestamps), bytes(4096))
        self.assertEqual(region._eof, 2*4096)

        self.assertEqual(region.chunk_info(1,2), (0, 0, 0, None))

    def test_set_chunk(self):
        region = Region()
        region.set_chunk(1,2, nbt.TAG_Int(3))
        self.assertEqual(region.chunk_info(1,2), (0, 0, 0, None))

    def test_region(self):
        region = Region.open("test/data/region-r.0.0.mca")
        info = region.chunk_info(1,2)
        chunk = region.parse_chunk(1,2)
        # print(chunk.Level.Entities.export())
        # print(chunk.Level.export(scope=['xPos', 'zPos']))

    def test_chunk_iterator(self):
        region = Region.open("test/data/region-r.0.0.mca")
        with region.chunk(1,2) as chunk:
          print(chunk)
        # print(chunk.Level.Entities.export())
        # print(chunk.Level.export(scope=['xPos', 'zPos']))
