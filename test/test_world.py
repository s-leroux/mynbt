import unittest
import os.path
from pprint import pprint

import mynbt.world as world

MC_SAMPLE_WORLD=os.path.join('test','data','MC-1_14_4-World')

class TestLocator(unittest.TestCase):
    def setUp(self):
        self.locator = world.Locator('.')

    def test_1(self):
        """ Should return path for standard files
        """
        self.assertEqual(self.locator.level(), os.path.join('.','level.dat'))
        self.assertEqual(self.locator.raids(), os.path.join('.','data','raids.dat'))
        self.assertEqual(self.locator.region(1,-2), os.path.join('.','region','r.1.-2.mca'))


class TestWorld(unittest.TestCase):
    def setUp(self):
        self.world = world.World(MC_SAMPLE_WORLD)

    def test_1(self):
        """ World can return a region
        """
        rx,rz = -1,-2
        cx,cz = 10,28

        region = self.world.region(rx,rz)
        self.assertIsNotNone(region)

        chunk = region.chunk[cx,cz]
        nbt = chunk.parse()
        self.assertEqual(nbt.Level.xPos, rx*32+cx)
        self.assertEqual(nbt.Level.zPos, rz*32+cz)

    def test_2(self):
        """ World can locate chunk in world coordinates
        """
        chunk = self.world.chunk(-22,-36)
        nbt = chunk.parse()
        self.assertEqual(nbt.Level.xPos, -22)
        self.assertEqual(nbt.Level.zPos, -36)

    def test_3(self):
        """ World can iterate over players
        """
        # XXX How to test that exactly?
        for player in self.world.players():
            _ = (player.filepath, player.Data.Version, [player.Data.SpawnX, player.Data.SpawnY, player.Data.SpawnZ])
