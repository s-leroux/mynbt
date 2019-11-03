import unittest
import os.path

from mynbt.poi import *

from test.data.region import *
from test.data.nbt import *

FILE = {
  'poi-r.0.0.mca': os.path.join('test','data','poi-r.0.0.mca'),
  'poi-copy.mca': os.path.join('test','tmp','poi-copy.mca'),
}

class TestPOIFromFile(unittest.TestCase):
    def test_1(self):
        """ Load POI file
        """
        poi = POI.fromFile(0,0,FILE['poi-r.0.0.mca'])
        for chunk in poi.chunks():
            self.assertEqual(chunk.parse().DataVersion, 1976)

class TestPOI(unittest.TestCase):
    RX=1
    RZ=2
    C1X=3
    C1Z=4
    C2X=5
    C2Z=6
    POI=REGION(10*PAGE_SIZE,
          CHUNK(C1X,C1Z,pageaddr=3,data=CHUNK_DATA(
              COMPOUND_FRAME(
                  WITH_NAME("Data", COMPOUND_FRAME)(
                      WITH_NAME("Sections", COMPOUND_FRAME)(
                          WITH_NAME("1", COMPOUND_FRAME)(
                              WITH_NAME("Records", LIST_FRAME)(
                                  COMPOUND,
                                  [
                                      WITH_NAME("pos",LIST_FRAME)(
                                          SHORT,
                                          [32*32*RX+32*C1X + 11, 0, 32*32*RZ+32*C1Z + 22]
                                      ),
                                  ]
                              ),
                          ),
                      ),
                  ),
              ),
          )),
      )

    def setUp(self):
        self.poi = POI(self.RX,self.RZ,self.POI)

    def test_1(self):
        self.poi.chunk[self.C2X,self.C2Z] = self.poi.chunk[self.C1X,self.C1Z]

        nbt = self.poi.chunk[self.C2X,self.C2Z].parse()
        pos = nbt.Data.Sections[1].Records[0].pos

        self.assertEqual(pos[0], 32*32*self.RX + 32*self.C2X + 11)
