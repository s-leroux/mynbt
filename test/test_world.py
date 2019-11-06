import unittest
import os.path
from pprint import pprint

import mynbt.world as world

MC_SAMPLE_WORLD=os.path.join('test','data','MC-1_14_4-World')

class TestUtilities(unittest.TestCase):
    def test_1(self):
        """ `partition` can split a range in world coordinates
            to a sequence of regions/chunk/sections
        """

        CASES=(
          dict(
              input=(range(1,8), range(2,7), range(3,6)),
              output={
                  (0,0): {
                      (0,0): [
                        (0, range(1,8),range(2,7), range(3,6))
                      ]
                  }
              },
          ),
          dict(
              input=(range(-16,0), range(1,16), range(-16, -2)),
              output={
                  (-1,-1): {
                      (31,31): [
                        (0, range(0,16), range(1,16), range(0,14))
                      ]
                  }
              },
          ),
          dict(
              input=(range(-8,-1), range(2,7), range(-6-32*16, -3-32*16)),
              output={
                  (-1,-2): {
                      (31,31): [
                        (0, range(8,15), range(2,7), range(10,13))
                      ]
                  }
              },
          ),
          dict(
              input=(range(1,22), range(2,7), range(3,6)),
              output={
                  (0,0): {
                      (0,0): [
                        (0, range(1,16),range(2,7), range(3,6)),
                      ],
                      (1,0): [
                        (0, range(0,6),range(2,7), range(3,6)),
                      ],
                  }
              },
          ),
          dict(
              input=(range(1,22), range(2,17), range(3,6)),
              output={
                  (0,0): {
                      (0,0): [
                        (0, range(1,16),range(2,16), range(3,6)),
                        (1, range(1,16),range(0,1), range(3,6)),
                      ],
                      (1,0): [
                        (0, range(0,6),range(2,16), range(3,6)),
                        (1, range(0,6),range(0,1), range(3,6)),
                      ],
                  }
              },
          ),
          dict(
              input=(range(1,22), range(2,17), range(3,18)),
              output={
                  (0,0): {
                      (0,0): [
                        (0, range( 1,16),range( 2,16), range( 3,16)),
                        (1, range( 1,16),range( 0, 1), range( 3,16)),
                      ],
                      (1,0): [
                        (0, range( 0, 6),range( 2,16), range( 3,16)),
                        (1, range( 0, 6),range( 0, 1), range( 3,16)),
                      ],
                      (0,1): [
                        (0, range( 1,16),range( 2,16), range( 0, 2)),
                        (1, range( 1,16),range( 0, 1), range( 0, 2)),
                      ],
                      (1,1): [
                        (0, range( 0, 6),range( 2,16), range( 0, 2)),
                        (1, range( 0, 6),range( 0, 1), range( 0, 2)),
                      ],
                  }
              },
          ),
        )

        for case in CASES:
            result = world.partition(*case['input'])
            self.assertEqual(result, case['output'], case['input'])

class TestLocator(unittest.TestCase):
    def setUp(self):
        self.locator = world.Locator('.')

    def test_1(self):
        """ Should return path for standard files
        """
        self.assertEqual(self.locator.level(), os.path.join('.','level.dat'))
        self.assertEqual(self.locator.raids(), os.path.join('.','data','raids.dat'))
        self.assertEqual(self.locator.region(1,-2), os.path.join('.','region','r.1.-2.mca'))
        self.assertEqual(self.locator.poi(1,-2), os.path.join('.','poi','r.1.-2.mca'))


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
