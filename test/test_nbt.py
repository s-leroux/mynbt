import unittest

from mynbt.nbt import *
SOME_SHORT = "".join((
  "02",                     # tag
  "00 09", b"shortTest".hex(),   # name
  "7F FF"                   # value
))
SOME_COMPOUND = "".join((
  "0A",                     # tag
  "00 04", b"Comp".hex(),   # name

  # payload
  SOME_SHORT,
  "00"                      #end
))
SOME_NESTED_COMPOUND = "".join((
  "0A",                     # tag
  "00 04", b"Data".hex(),   # name

  # payload
  SOME_SHORT,
  SOME_COMPOUND,
  "00"                      #end
))


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
        offset = t.parse_payload(data, offset)

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

class TestCompoundTag(unittest.TestCase):
    def test_keys(self):
        t = TAG.parse_file("test/data/level.dat")
        self.assertEqual(list(t.keys()), ['Data'])

    def test_get_attr(self):
        t = TAG.parse_file("test/data/level.dat")
        item = t.Data
        self.assertIn('DataPacks', list(item.keys()))
        self.assertIn('GameRules', list(item.keys()))

    def test_get_item(self):
        t = TAG.parse_file("test/data/level.dat")
        item = t['Data']
        self.assertIn('DataPacks', list(item.keys()))
        self.assertIn('GameRules', list(item.keys()))

    def test_get_value_in_compount(self):
        t, _ = TAG.parse(bytes.fromhex(SOME_COMPOUND), 0)
        self.assertEqual(t.shortTest, 32767)

    def test_get_value(self):
        t, _ = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertEqual(t.value, 32767)

    def test_nested_compound(self):
        t, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(t.name, 'Data')
        child = t.items['Comp']
        self.assertEqual(child.name, 'Comp')

import gzip
class TestCache(unittest.TestCase):
    def test_compound_cache(self):
        with gzip.open("test/data/level.dat", "rb") as f:
          data = f.read()
          t, offset = TAG.parse(data, 0)

        self.assertEqual(t.cache, data)

    def test_parent_tracking(self):
        """ Nested elements shoud track their parent as weak links
        """
        t, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        child = t.items['Comp']
        data = t.items['shortTest']

        self.assertEqual([*child.parents], [t])
        del t
        self.assertEqual([*child.parents], [])

    def test_invalidate(self):
        """ Invalidte should invalidate the whole ancestors chain
        """
        t, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        child1 = t.items['Comp']
        child2 = t.items['shortTest']
        data = child1.items['shortTest']

        data.invalidate()

        # print(t)
        # print(child1)
        # print(child2)
        # print(data)

        self.assertIsNone(data.cache)
        self.assertIsNone(child1.cache)
        self.assertIsNotNone(child2.cache)
        self.assertIsNone(t.cache)

