import unittest
import os.path

import mynbt.world as world

class TestLocator(unittest.TestCase):
    def setUp(self):
        self.locator = world.Locator('.')

    def test_1(self):
        """ Should return path for standard files
        """
        self.assertEqual(self.locator.level, os.path.join('.','level.dat'))
        self.assertEqual(self.locator.poi, os.path.join('.','poi.dat'))
