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

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            region = Region(broken_header.to_bytes(4, 'big'))
            chunk = region.chunk_info(0,0)

        self.assertEqual([chunk.addr,chunk.size], [addr, size])
        self.assertEqual(chunk.data, EMPTY_PAGE*size)

    def test_4(self):
        """ Region should compute logical page usage bitmap
        """
        region = Region(REGION(5*1024*1024,
          CHUNK(3,4,pageaddr=5,pagecount=2,data=UTF8("some data")),
        ))

        bitmap = region.bitmap()
        self.assertSequenceEqual(bitmap, ((),(),(),(),(), ((3,4),), ((3,4),)))
        #                                  0  1  2  3  4   5        6

    def test_5(self):
        """ Region bitmap should trace overlapping chunks
        """
        region = Region(REGION(5*1024*1024,
          CHUNK(0,1,pageaddr=4,pagecount=2,data=UTF8("some data")),
          CHUNK(3,4,pageaddr=5,pagecount=2,data=UTF8("other data")),
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
              CHUNK(3,4,pageaddr=1,pagecount=2,data=UTF8("some data")),
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

        self.assertEqual(region.chunk_info(1,2), (None, None, 0, 0, 0, b""))

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
            SHORT_FRAME(123)
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

    def test_chunk_contextmanager(self):
        region = Region(REGION(10*PAGE_SIZE,
          CHUNK(1,2,pageaddr=3,data=CHUNK_DATA(
            COMPOUND_FRAME(
              INT_FRAME(123, "data")
            )
          )),
        ))
        with region.chunk(1,2).parse() as nbt:
            nbt.data = 12

        self.assertEqual(region.parse_chunk(1,2).data, 12)

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

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("error")

            region = Region.open('test/tmp/dump.bin')
            chunk = region.parse_chunk(1,2)
            # print(chunk)

class TestRegionEdgeCases(unittest.TestCase):
    R = REGION(10*PAGE_SIZE,
      CHUNK(3,4,pageaddr=3,data=CHUNK_DATA(
          COMPOUND_FRAME(
              WITH_NAME("d1", COMPOUND_FRAME)(
                SHORT_FRAME(56, "a"),
              ),
              WITH_NAME("d2", COMPOUND_FRAME)(
                  WITH_NAME("d21", COMPOUND_FRAME)(
                    INT_FRAME(78, "b"),
                  ),
              ),
          )
      )),
    )

    def setUp(self):
        self.root = Region(self.R)

    def test_1(self):
        """ Parsing a non-existant chunk should
            return None
        """
        nbt = self.root.parse_chunk(5,5)
        self.assertIsNone(nbt)

    def test_2(self):
        """ In a context manager, parsing a non-existant chunk should
            return None
        """
        with self.assertRaises(EmptyChunkError) as cm:
            with self.root.chunk(5,5).parse() as nbt:
                self.assertIsNone(nbt)

    def test_3(self):
        """ Region should not break on loading damaged files
        """
        region = Region.open('test/data/broken-r.-1.-1.mca')
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            # this file has 3 page used by multiple chunks:
            #
            # DuplicatePage: Page 1168 of test/data/broken-r.-1.-1.mca is used by multiple chunks: ((28, 8), (17, 14))
            # DuplicatePage: Page 1297 of test/data/broken-r.-1.-1.mca is used by multiple chunks: ((22, 6), (22, 9))
            # DuplicatePage: Page 1298 of test/data/broken-r.-1.-1.mca is used by multiple chunks: ((22, 6), (22, 9))
            #
            region.check()

        self.assertEqual(len(w), 3)
        for it in w:
            self.assertIs(type(it.message), DuplicatePage)

    def test_4(self):
        """ Region should load "broken" chunks
        """
        region = Region.open('test/data/broken-r.-1.-1.mca')

        #
        # chunk (17,14) points to garbage data
        #
        with self.assertRaises(BadChunkError) as cm:
            nbt = region.parse_chunk(17,14)

        #
        # Chunk (22,9) points to data belonging to another chunk
        #
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")

            nbt = region.parse_chunk(22,9)

        self.assertEqual([type(it.message) for it in w], [InconsistentLocation])


class TestInterRegion(unittest.TestCase):
    R1 = REGION(10*PAGE_SIZE,
      CHUNK(1,2,pageaddr=3,data=CHUNK_DATA(
          COMPOUND_FRAME(
              WITH_NAME("r1d1", COMPOUND_FRAME)(
                SHORT_FRAME(12, "a"),
              ),
              WITH_NAME("r1d2", COMPOUND_FRAME)(
                  WITH_NAME("r1d21", COMPOUND_FRAME)(
                    INT_FRAME(34, "b"),
                  ),
              ),
          ),
      )),
    )

    R2 = REGION(10*PAGE_SIZE,
      CHUNK(3,4,pageaddr=3,data=CHUNK_DATA(
          COMPOUND_FRAME(
              WITH_NAME("r2d1", COMPOUND_FRAME)(
                SHORT_FRAME(56, "a"),
              ),
              WITH_NAME("r2d2", COMPOUND_FRAME)(
                  WITH_NAME("r2d21", COMPOUND_FRAME)(
                    INT_FRAME(78, "b"),
                  ),
              ),
          )
      )),
    )

    def setUp(self):
        self.r1 = Region(self.R1)
        self.r2 = Region(self.R2)

    def test_1(self):
        """ Chunk raw data overwrite chunks in another region
        """

        chunk = self.r1.get_chunk(1,2)
        self.r2.set_chunk(1,2,chunk)

        nbt = self.r2.parse_chunk(1,2)
        self.assertEqual(nbt.r1d1.a, 12)

    def test_2(self):
        """ Chunk raw data can be copied between regions
        """

        chunk = self.r1.get_chunk(1,2)
        self.r2.set_chunk(3,4,chunk)

        nbt = self.r2.parse_chunk(3,4)
        self.assertEqual(nbt.r1d1.a, 12)

    def test_3(self):
        """ Context managers can be used to copy data between
            regions
        """
        with self.r1.chunk(1,2).parse() as nbt1:
            with self.r2.chunk(3,4).parse() as nbt2:
                nbt1.r1d1 = nbt2.r2d2

        result = self.r1.parse_chunk(1,2)
        self.assertEqual(result.r1d1.r2d21.b, 78)


class TestChunks(unittest.TestCase):
    R = REGION(10*PAGE_SIZE,
      CHUNK(1,2,pageaddr=3,data=CHUNK_DATA(
          STRING_FRAME("Chunk 1,2", "data"),
      )),
      CHUNK(3,3,pageaddr=4,data=CHUNK_DATA(
          STRING_FRAME("Chunk 3,3", "data"),
      )),
      CHUNK(3,4,pageaddr=5,data=
          STRING("** BAD CHUNK **"),
      ),
      CHUNK(3,5,pageaddr=6,data=CHUNK_DATA(
          STRING_FRAME("Chunk 3,5 [change me]", "data"),
      )),
      CHUNK(6,6,pageaddr=7,data=CHUNK_DATA(
          STRING_FRAME("Chunk 6,6 [set to garbage]", "data"),
      )),
      CHUNK(6,7,pageaddr=8,data=CHUNK_DATA(
          STRING_FRAME("Chunk 6,7 [kill me]", "data"),
      )),
      CHUNK(6,8,pageaddr=9,data=CHUNK_DATA(
          STRING_FRAME("Chunk 6,8", "data"),
      )),
    )

    def setUp(self):
        self.region = Region(self.R)
        self.region.set_chunk(3,5, bytes.fromhex(CHUNK_DATA(STRING_FRAME("Updated chunk 3,5"))))
        self.region.set_chunk(6,6, b"** BAD CHUNK **")
        self.region.kill_chunk(6,7)


    def test_1(self):
        """ Chunk raw data overwrite chunks in another region
        """

        with warnings.catch_warnings(record=True):
            chunks = [(chunk.x, chunk.z) for chunk in self.region.chunks()]

        self.assertSequenceEqual(chunks, [
          (1,2), (3,3), (3,5), (6,8)
        ])

        # with warnings.catch_warnings(record=True):
        #     for chunk in self.region.chunks():
        #         print(chunk)
