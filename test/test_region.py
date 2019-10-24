import unittest
import warnings

from io import BytesIO
from mynbt.region import *
from test.data.region import *
from test.data.nbt import *
import mynbt.nbt as nbt

class TestRegion(unittest.TestCase):
    def test_1(self):
        """ Region without data should have all chunks empty
        """
        region = Region()
        chunks = [region.chunk_info(x,y) for x in range(32) for y in range(32)]
        self.assertSequenceEqual(chunks, [EMPTY_CHUNK]*32*32)

    def test_2(self):
        """ Region with incomplete headers should be silently fixed
        """
        region = Region(b"\x00"*(PAGE_SIZE//2))
        chunks = [region.chunk_info(x,y) for x in range(32) for y in range(32)]
        self.assertSequenceEqual(chunks, [EMPTY_CHUNK]*32*32)

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
        """ Region should compute logical page usage bitmap
        """
        region = Region(REGION(5*1024*1024,
          CHUNK(3,4,pageaddr=5,pagecount=2,data=b"some data"),
        ))

        bitmap = region.bitmap()
        self.assertSequenceEqual(bitmap, ((),(),(),(),(), ((3,4),), ((3,4),)))
        #                                  0  1  2  3  4   5        6

    def test_5(self):
        """ Region bitmap should trace overlapping chunks
        """
        region = Region(REGION(5*1024*1024,
          CHUNK(0,1,pageaddr=4,pagecount=2,data=b"some data"),
          CHUNK(3,4,pageaddr=5,pagecount=2,data=b"other data"),
        ))

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            bitmap = region.bitmap()
            self.assertSequenceEqual(bitmap, ((),(),(),(),((0,1),), ((0,1),(3,4),), ((3,4),)))
            #                                  0  1  2  3  4         5                6

            self.assertEqual(len(w), 1)

    def test_6(self):
        """ Region should warn about odd chunk data location
        """

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            region = Region(REGION(5*1024*1024,
              # at page 1, date are in the region header
              CHUNK(3,4,pageaddr=1,pagecount=2,data=b"some data"),
            ))

            self.assertEqual(len(w), 1)

    def test_7(self):
        """ Region can return raw chunk data
        """
        data=b"some random data"
        region = Region(REGION(5*1024*1024,
          CHUNK(3,4,pageaddr=5,pagecount=2,data=data),
        ))

        content = region.get_chunk(3,4)
        self.assertTrue(bytes(content).startswith(data))
        self.assertTrue(len(content)%PAGE_SIZE == 0)

    def test_8(self):
        """ Region can copy raw chunk data
        """
        data=b"some random data"
        region = Region(REGION(5*1024*1024,
          CHUNK(3,4,pageaddr=5,pagecount=2,data=data),
        ))

        region.copy_chunk(3,4,5,6)
        content = region.get_chunk(3,4)
        self.assertTrue(bytes(content).startswith(data))
        self.assertTrue(len(content)%PAGE_SIZE == 0)
        content = region.get_chunk(5,6)
        self.assertTrue(bytes(content).startswith(data))
        self.assertTrue(len(content)%PAGE_SIZE == 0)

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

    def test_write_chunk(self):
        region = Region()
        region.write_chunk(1,2, nbt.Integer(3))
        chunk = region.chunk_info(1,2)
        self.assertEqual((chunk.x,chunk.z), (1, 2))
        self.assertGreater(len(chunk.data), 0)

    def test_kill_chunk(self):
        region = Region(REGION(10*PAGE_SIZE,
          CHUNK(1,2,pageaddr=3,data=CHUNK_DATA(
            SHORT_FRAME(123).BYTES
          )),
          CHUNK(2,1,pageaddr=5,data=CHUNK_DATA(
            SHORT_FRAME(456).BYTES
          )),
        ))
        self.assertEqual(region.bitmap(), [(), (), (), ((1,2),), (), ((2, 1),)])
        region.kill_chunk(1,2)
        self.assertEqual(region.bitmap(), [(), (), (), (), (), ((2, 1),)])

    def test_parse_chunk(self):
        region = Region(REGION(10*PAGE_SIZE,
          CHUNK(1,2,pageaddr=4,pagecount=2,data=CHUNK_DATA(
            SHORT_FRAME(123).BYTES
          )),
        ))
        nbt = region.parse_chunk(1,2)
        self.assertEqual(nbt, 123)

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
        region.write_chunk(1,2, nbt.Integer(3))


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
