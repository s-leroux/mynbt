import unittest

from mynbt.nbt import *
SOME_BYTE = "".join((
  "01",                     # tag
  "00 08", b"byteTest".hex(),   # name
  "7F"                      # value
))
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
  SOME_BYTE,
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
EMPTY_COMPOUND = "".join((
  "0A",                     # tag
  "00 05", b"Empty".hex(),  # name
  "00"                      #end
))
SOME_LIST = "".join((
  "09"
  "00 04", b"List".hex(),
  "02",                     # paylod tag id
  "00 00 00 04"             # count
  "00 00",
  "00 01",
  "00 02",
  "00 03",
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
        payload, offset = t.parse_payload(data, offset)

        self.assertEqual(data[offset:], b"")
        self.assertEqual(id, 2)
        self.assertEqual(name, "shortTest")
        self.assertEqual(payload, bytes.fromhex("7F FF"))

class TestParseTags(unittest.TestCase):
    def test_parse_end(self):
        t, name, offset = TAG.parse(bytes.fromhex("00"), 0)
        self.assertIsInstance(t, TAG_End)
        self.assertEqual(t._id, 0)

    def test_parse_short(self):
        t,name, offset = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertIsInstance(t, TAG_Short)
        self.assertEqual(t._id, 2)
        self.assertEqual(name, "shortTest")
        self.assertEqual(bytes(t._payload), bytes.fromhex("7F FF"))

class TestParseFiles(unittest.TestCase):
    def test_parse_level(self):
        """ It should load uncompressed NBT files
        """
        t = TAG.parse_file("test/data/level.dat")
        self.assertIsInstance(t, TAG_Compound)

    def test_parse_server(self):
        """ It should load uncompressed NBT files
        """
        t = TAG.parse_file("test/data/servers.dat")
        self.assertIsInstance(t, TAG_Compound)

class TestListTag(unittest.TestCase):
    def test_parse_list(self):
        data = bytes.fromhex(SOME_LIST + "FF")
        nbt, name, offset = TAG.parse(data, 0)
        self.assertEqual(data[offset:], b"\xFF")
        self.assertIsInstance(nbt, TAG_List)
        self.assertEqual(len(nbt), 4)
        self.assertEqual(nbt[0].value, 0)
        self.assertEqual(nbt[1].value, 1)
        self.assertEqual(nbt[2].value, 2)
        self.assertEqual(nbt[3].value, 3)
        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4].value, 4)

    def test_set_item(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        val, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)

        self.assertIsNot(nbt[0], val)
        self.assertIsNotNone(nbt._payload)
        nbt[0] = val
        self.assertIs(nbt[0], val)
        self.assertIsNone(nbt._payload)

    def test_append(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        val, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)

        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4].value, 4)
        self.assertIsNotNone(nbt._payload)

        nbt.append(val)

        self.assertIs(nbt[4], val)
        self.assertIsNone(nbt._payload)

    def test_del_item(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        self.assertEqual(len(nbt), 4)
        self.assertEqual(nbt[0].value, 0)
        self.assertEqual(nbt[1].value, 1)
        self.assertEqual(nbt[2].value, 2)
        self.assertEqual(nbt[3].value, 3)
        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4].value, 4)

        del nbt[1]
        
        self.assertIsNone(nbt._payload)
        self.assertEqual(len(nbt), 3)
        self.assertEqual(nbt[0].value, 0)
        self.assertEqual(nbt[1].value, 2)
        self.assertEqual(nbt[2].value, 3)
        with self.assertRaises(IndexError):
          self.assertEqual(nbt[3].value, 4)

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
        t, _, _ = TAG.parse(bytes.fromhex(SOME_COMPOUND), 0)
        self.assertEqual(t.shortTest.value, 32767)

    def test_get_value(self):
        t, _, _ = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertEqual(t.value, 32767)

    def test_nested_compound(self):
        t, name, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(name, 'Data')
        child = t._items['Comp']

    def test_path(self):
        t, *_ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(t.Comp.shortTest.value, 32767)

    def test_del_item(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(len(nbt.Comp), 2)
        self.assertEqual(nbt.Comp['byteTest'].value, 127)
        self.assertEqual(nbt.Comp['shortTest'].value, 32767)

        del nbt.Comp.shortTest
        
        self.assertIsNone(nbt._payload)
        self.assertEqual(len(nbt.Comp), 1)
        self.assertEqual(nbt.Comp['byteTest'].value, 127)
        with self.assertRaises(KeyError):
          self.assertEqual(nbt.Comp['shortTest'].value, 32767)

class TestExport(unittest.TestCase):
    CASES = (
      dict(dump=SOME_SHORT, value=32767, extended={'type': 'TAG_Short', 'value': 32767}),
      dict(dump=SOME_COMPOUND, value=dict(shortTest=32767, byteTest=127), extended=dict(type='TAG_Compound', value={'shortTest': {'type': 'TAG_Short', 'value': 32767}, 'byteTest':{'type':'TAG_Byte', 'value':127}})),
    )

    def test_export_short(self):
        for case in self.CASES:
          t, *_ = TAG.parse(bytes.fromhex(case['dump']), 0)

          x = t.export()
          self.assertEqual(x, case['value'])

          x = t.export(compact=True)
          self.assertEqual(x, case['value'])

          x = t.export(compact=False)
          self.assertEqual(x, case['extended'])


import gzip
class TestCache(unittest.TestCase):
    def test_compound_cache(self):
        with gzip.open("test/data/level.dat", "rb") as f:
          data = f.read()
          t, _, offset = TAG.parse(data, 0)

        self.assertEqual(bytes(t._payload), data[3:])

    def test_parent_tracking(self):
        """ Nested elements shoud track their parent as weak links
        """
        t, *_ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        child = t._items['Comp']
        data = t._items['shortTest']

        self.assertEqual([*child._parents], [t])
        del t
        self.assertEqual([*child._parents], [])

    def test_invalidate(self):
        """ Invalidte should invalidate the whole ancestors chain
        """
        t, *_ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        child1 = t._items['Comp']
        child2 = t._items['shortTest']
        data = child1._items['shortTest']

        data.invalidate()

        # print(t)
        # print(child1)
        # print(child2)
        # print(data)

        self.assertIsNone(data._payload)
        self.assertIsNone(child1._payload)
        self.assertIsNotNone(child2._payload)
        self.assertIsNone(t._payload)

class TestSetValue(unittest.TestCase):
    def test_set_value_atom_fail(self):
        """ Atomic values should be immutable
        """
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)
        with self.assertRaises(AttributeError):
            nbt.value = 0

    def test_set_value_compound(self):
        """ Compound items can be updated
        """
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_COMPOUND), 0)
        val, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)

        nbt.x = val
        self.assertIn("x", nbt.keys())
        self.assertIs(val.value, nbt.x.value)

    def test_copy(self):
        """ Items can be copied between compounds
        """
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_COMPOUND), 0)
        other, *_ = TAG.parse(bytes.fromhex(EMPTY_COMPOUND), 0)

        other.x = nbt.shortTest
        self.assertIn("x", other.keys())
        self.assertIs(nbt.shortTest, other.x)
