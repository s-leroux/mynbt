import unittest

from mynbt.region import *

class TestRegion(unittest.TestCase):
    def test_bytes_to_chunk_addr(self):
        addr = bytes_to_chunk_addr(bytes.fromhex("102030405060"), 0)
        self.assertEqual(addr, (4096*0x102030, 4096*0x40))

        addr = bytes_to_chunk_addr(bytes.fromhex("DEADBEEF102030405060"), 4)
        self.assertEqual(addr, (4096*0x102030, 4096*0x40))

    def test_region(self):
        region = Region.open("test/data/region-r.0.0.mca")
        info = region.chunk_info(1,2)
        chunk = region.chunk(1,2)
        print(chunk.Level.Entities.export())
        print(chunk.Level.export(scope=['xPos', 'zPos']))
