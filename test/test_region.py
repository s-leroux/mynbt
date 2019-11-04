import unittest
import os.path

from mynbt.region import *
from test.data.region import *
from test.data.nbt import *

FILE = {
  'simplechunk.mca': os.path.join('test','data','simplechunk-r.0.0.mca'),
}


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
              WITH_NAME("Level",COMPOUND_FRAME)(
                  INT_FRAME(32*RX+C1X, "xPos"),
                  INT_FRAME(32*RZ+C1Z, "zPos"),
                  WITH_NAME("Entities",LIST_FRAME)(
                      COMPOUND,
                      [
                          WITH_NAME("Pos",LIST_FRAME)(
                              SHORT,
                              [16*32*RX+16*C1X + 11, 0, 16*32*RZ+16*C1Z + 7]
                          ),
                      ]
                  ),
              ),
          ),
      )),
      CHUNK(C2X,C2Z,pageaddr=4,data=CHUNK_DATA(
          COMPOUND_FRAME(
              WITH_NAME("Level",COMPOUND_FRAME)(
                  STRING_FRAME("Chunk 3,4", "n"),
                  INT_FRAME(32*RX+C2X, "xPos"),
                  INT_FRAME(32*RZ+C2Z, "zPos"),
              ),
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
        self.assertEqual(nbt.Level.xPos, 32*self.RX+self.C2X)
        self.assertEqual(nbt.Level.zPos, 32*self.RZ+self.C2Z)


    def test_2(self):
        """ Region can copy chunks and update entities pos
        """
        self.region.chunk[self.C2X,self.C2Z] = self.region.chunk[self.C1X,self.C1Z]

        nbt = self.region.chunk[self.C2X,self.C2Z].parse()
        self.assertEqual(nbt.Level.Entities[0].Pos[0], 16*32*self.RX + 16*self.C2X + 11)
        self.assertEqual(nbt.Level.Entities[0].Pos[2], 16*32*self.RZ + 16*self.C2Z + 7)

class TestAccessors(unittest.TestCase):
    def setUp(self):
        self.region = Region.fromFile(0,0,FILE['simplechunk.mca'])
        self.chunk = next(self.region.chunks())
        self.nbt = self.chunk.parse()

    def test_1(self):
        """ Region should attach a section iterator to nbt
        """
        for section in self.nbt.sections():
            self.assertIsNotNone(section.y)

    def test_2(self):
        """ Region should attach a section accessor to nbt
        """
        N=3
        section = self.nbt.section[N]
        self.assertEqual(section.y, N)
