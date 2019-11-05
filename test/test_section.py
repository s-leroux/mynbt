import unittest

from mynbt.section import *

from test.data.simplechunk import SECTION

class TestUtils(unittest.TestCase):
    def test_1(self):
        """ pos2idx and idx2pos should perform
            reverse operations
        """
        for t in ((0,0,0), (1,2,3), (15,15,15)):
            self.assertEqual(t, idx2pos(pos2idx(*t)))

    def test_2(self):
        """ pos2idx should convert X,Y,Z positions to indices
        """
        for k,v in {0:(0,0,0), 1+2*256+3*16: (1,2,3)}.items():
            self.assertEqual(k, pos2idx(*v))
            self.assertEqual(v, idx2pos(k))



class TestSection(unittest.TestCase):
    def setUp(self):
        self.section = Section.fromNBT(0,0,SECTION)

    def test_1(self):
        """ Section can load data from NBT
        """
        self.assertEqual(self.section.y, SECTION['Y'])
        self.assertEqual(self.section._palette, SECTION['Palette'])
        # print(self.section._palette)
        # print(self.section._blocks)
        for i,n in enumerate(self.section._blocks):
            self.assertTrue(0 <= n < len(self.section._palette))

    def test_2(self):
        """ Section.block returns a block by coordinates
        """
        block = self.section.block(32%16, 90%16, 16%16)
        self.assertEqual(block['Name'], "minecraft:magma_block")

        block = self.section.block(47%16, 90%16, 16%16)
        self.assertEqual(block['Name'], "minecraft:glass")

        block = self.section.block(47%16, 90%16, 31%16)
        self.assertEqual(block['Name'], "minecraft:stone")


