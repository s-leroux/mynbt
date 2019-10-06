import unittest

from mynbt.nbt import *

class TestTags(unittest.TestCase):
    def test_TAG_End(self):
        t = TAG_End()
        r = t.consume(bytes.fromhex("00"))

        self.assertEqual(r, b"")
        self.assertEqual(t.id, 0)

    def test_TAG_Short(self):
        t = TAG_Short()
        r = t.consume(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"))

        self.assertEqual(r, b"")
        self.assertEqual(t.id, 2)
        self.assertEqual(t.name, "shortTest")
        self.assertEqual(t.payload, bytes.fromhex("7F FF"))

class TestParseTags(unittest.TestCase):
    def test_parse(self):
        t = TAG.parse(bytes.fromhex("00"))
        self.assertIsInstance(t, TAG_End)
        self.assertEqual(t.id, 0)

        t = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"))
        self.assertIsInstance(t, TAG_Short)
        self.assertEqual(t.id, 2)
        self.assertEqual(t.name, "shortTest")
        self.assertEqual(t.payload, bytes.fromhex("7F FF"))
