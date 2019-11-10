import unittest

from mynbt.section import *
import mynbt.nbt as nbt
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
        self.section = Section.fromNBT(0,0,nbt.Node.fromNativeObject(SECTION))

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

    def test_3(self):
        """ block_state_index should return the index of existing blocks
        """
        for blk_name in ("minecraft:stone", "minecraft:air", "minecraft:obsidian"):
            idx = self.section.block_state_index(Name=blk_name)
            self.assertEqual(self.section._palette[idx]['Name'], blk_name)

    def test_4(self):
        """ Sections can fill block areas
        """
        xrange = range(5,10)
        yrange = range(5,10)
        zrange = range(5,10)
        self.section.fill(xrange, yrange, zrange, Name="minecraft:dirt")
        idx = self.section.block_state_index(Name="minecraft:dirt")
        
        self.assertEqual(len([blk for blk in self.section._blocks if blk == idx]), len(xrange)*len(yrange)*len(zrange))
     
        for x in xrange:
            for y in yrange:
                for z in zrange:
                    self.assertEqual(self.section.block(x,y,z)['Name'], "minecraft:dirt")
