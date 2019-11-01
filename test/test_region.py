import unittest

from mynbt.region import *
from test.data.region import *
from test.data.nbt import *

class TestRegion(unittest.TestCase):
    RX = 10
    RZ = 20
    C1X = 1
    C1Z = 2
    C2X = 3
    C2Z = 4

    R = REGION(10*PAGE_SIZE,
      CHUNK(C1X,C1Z,pageaddr=3,data=CHUNK_DATA(
          COMPOUND_FRAME(
              STRING_FRAME("Chunk 1,2", "n"),
              INT_FRAME(32*RX+C1X, "xPos"),
              INT_FRAME(32*RZ+C1Z, "zPos"),
              WITH_NAME("Level",COMPOUND_FRAME)(
                  WITH_NAME("Entities",LIST_FRAME)(
                      COMPOUND,
                      [
                          WITH_NAME("Pos",LIST_FRAME)(
                              SHORT,
                              [32*32*RX+32*C1X + 11, 0, 32*32*RZ+32*C1Z + 22]
                          ),
                      ]
                  ),
              ),
          ),
      )),
      CHUNK(C2X,C2Z,pageaddr=4,data=CHUNK_DATA(
          COMPOUND_FRAME(
              STRING_FRAME("Chunk 3,4", "n"),
              INT_FRAME(32*RX+C2X, "xPos"),
              INT_FRAME(32*RZ+C2Z, "zPos"),
          ),
      )),
    )

    def setUp(self):
        self.region = Region(self.RX, self.RZ, self.R)

    def test_1(self):
        """ Region can copy chunks and update xPos and zPos
        """
        self.region.chunk[self.C2X,self.C2Z] = self.region.chunk[self.C1X,self.C1Z]

        nbt = self.region.chunk[self.C2X,self.C2Z].parse()
        self.assertEqual(nbt.n, "Chunk 1,2")
        self.assertEqual(nbt.xPos, 32*self.RX+self.C2X)
        self.assertEqual(nbt.zPos, 32*self.RZ+self.C2Z)


    def test_2(self):
        """ Region can copy chunks and update entities pos
        """
        self.region.chunk[self.C2X,self.C2Z] = self.region.chunk[self.C1X,self.C1Z]

        nbt = self.region.chunk[self.C2X,self.C2Z].parse()
        self.assertEqual(nbt.Level.Entities[0].Pos[0], 32*32*self.RX + 32*self.C2X + 11)
        self.assertEqual(nbt.Level.Entities[0].Pos[2], 32*32*self.RZ + 32*self.C2Z + 22)

