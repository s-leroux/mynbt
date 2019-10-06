import unittest

from mynbt.nbt import *

class TestTags(unittest.TestCase):
    def test_TAG_End(self):
        t = TAG_End()
        data = bytes.fromhex("00")
        offset = 0
        id, offset = t.parse_id(data, offset)

        self.assertEqual(data[offset:], b"")
        self.assertEqual(id, 0)

    def test_TAG_Short(self):
        t = TAG_Short()
        data = bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF")
        offset = 0
        id, offset = t.parse_id(data, offset)
        name, offset = t.parse_name(data, offset)
        payload, offset = t.parse_payload(data, offset)

        self.assertEqual(data[offset:], b"")
        self.assertEqual(id, 2)
        self.assertEqual(name, "shortTest")
        #self.assertEqual(payload, bytes.fromhex("7F FF"))

class TestParseTags(unittest.TestCase):
    def test_parse_end(self):
        t, offset = TAG.parse(bytes.fromhex("00"), 0)
        self.assertIsInstance(t, TAG_End)
        self.assertEqual(t.id, 0)

    def test_parse_short(self):
        t, offset = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertIsInstance(t, TAG_Short)
        self.assertEqual(t.id, 2)
        self.assertEqual(t.name, "shortTest")
        #self.assertEqual(t.payload, bytes.fromhex("7F FF"))

    def test_parse_list(self):
        data = bytes.fromhex("09  00 04 4c 69 73 74  01 00 00 00 02  01  02  FF")
        t, offset = TAG.parse(data, 0)
        self.assertEqual(data[offset:], b"\xFF")
        self.assertIsInstance(t, TAG_List)
        #self.assertEqual(len(t.payload), 2)

class TestParseFiles(unittest.TestCase):
    def test_parse_level(self):
        t = TAG.parse_file("test/data/level.dat")
        self.assertIsInstance(t, TAG_Compound)

import gzip
class TestCache(unittest.TestCase):
    def test_compound_cache(self):
        with gzip.open("test/data/level.dat", "rb") as f:
          data = f.read()
          t, offset = TAG.parse(data, 0)

        self.assertEqual(t.cache, data)



