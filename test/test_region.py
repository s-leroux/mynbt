import unittest

from mynbt.region import *
from test.data.region import *
from test.data.nbt import *

class TestRegion(unittest.TestCase):
    RX = 10
    RZ = 20
    R = REGION(10*PAGE_SIZE,
      CHUNK(1,2,pageaddr=3,data=CHUNK_DATA(
          COMPOUND_FRAME(
              STRING_FRAME("Chunk 1,2", "n"),
              INT_FRAME(32*RX+1, "xPos"),
              INT_FRAME(32*RZ+2, "zPos"),
          ),
      )),
      CHUNK(3,4,pageaddr=4,data=CHUNK_DATA(
          COMPOUND_FRAME(
              STRING_FRAME("Chunk 3,4", "n"),
              INT_FRAME(32*RX+3, "xPos"),
              INT_FRAME(32*RZ+4, "zPos"),
          ),
      )),
    )

    def setUp(self):
        self.region = Region(self.RX, self.RZ, self.R)

    def test_1(self):
        """ Region can copy chunks
        """
        self.region.chunk[3,4] = self.region.chunk[1,2]

        nbt = self.region.chunk[3,4].parse()
        self.assertEqual(nbt.n, "Chunk 1,2")
        self.assertEqual(nbt.xPos, 320+3)
        self.assertEqual(nbt.zPos, 640+4)

