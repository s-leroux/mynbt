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

class TestNodeComparisons(unittest.TestCase):
    def test_1(self):
        """ Atomic values should be equal to themselves
        """

        val = Integer(3)
        self.assertEqual(val, val)

    def test_2(self):
        """ Atomic values should be equal to other atomic
            value of same type and same value
        """

        val1 = Integer(3)
        val2 = Integer(3)
        val3 = Integer(4)
        self.assertIsNot(val1, val2)
        self.assertEqual(val1, val2)
        self.assertNotEqual(val1, val3)

    def test_3(self):
        """ Compatible Atomic values of different types
            should be comparable
        """

        int1 = Integer(3)
        int2 = Integer(4)
        float1 = Float(3.0)
        float2 = Float(4.0)

        # Ensure the comparison works with native types
        self.assertEqual(3.0, 3)
        self.assertEqual(4.0, 4)

        # the real tests
        self.assertEqual(int1, float1)
        self.assertEqual(int2, float2)
        self.assertNotEqual(int1, float2)
        self.assertNotEqual(int2, float1)

    def test_4(self):
        """ Proxies should be equal to themselves
        """
        
        p = AtomProxy(trait=ByteTrait, payload=b"\xFF")
        self.assertEqual(p,p)

    def test_5(self):
        """ Proxies should be comparable to Atomic values
        """
        int1 = Integer(3)
        int2 = Integer(4)
        proxy1 = AtomProxy(trait=ByteTrait, payload=b"\x03")
        proxy2 = AtomProxy(trait=ByteTrait, payload=b"\x04")

        self.assertEqual(int1, proxy1)
        self.assertEqual(int2, proxy2)
        self.assertNotEqual(int1, proxy2)
        self.assertNotEqual(int2, proxy1)
        # swap tests
        self.assertEqual(proxy1, int1)
        self.assertEqual(proxy2, int2)
        self.assertNotEqual(proxy2, int1)
        self.assertNotEqual(proxy1, int2)

    def test_6(self):
        """ Atomic values should be comparable to native values
        """

        int1 = Integer(3)
        int2 = Integer(4)
        native1 = 3
        native2 = 4

        self.assertEqual(int1, native1)
        self.assertEqual(int2, native2)
        self.assertNotEqual(int1, native2)
        self.assertNotEqual(int2, native1)
        # swap tests
        self.assertEqual(native1, int1)
        self.assertEqual(native2, int2)
        self.assertNotEqual(native2, int1)
        self.assertNotEqual(native1, int2)

    def test_7(self):
        """ Proxies should be comparable to native values
        """
        native1 = 3
        native2 = 4
        proxy1 = AtomProxy(trait=ByteTrait, payload=b"\x03")
        proxy2 = AtomProxy(trait=ByteTrait, payload=b"\x04")

        self.assertEqual(native1, proxy1)
        self.assertEqual(native2, proxy2)
        self.assertNotEqual(native1, proxy2)
        self.assertNotEqual(native2, proxy1)
        # swap tests
        self.assertEqual(proxy1, native1)
        self.assertEqual(proxy2, native2)
        self.assertNotEqual(proxy2, native1)
        self.assertNotEqual(proxy1, native2)

class TestParsing(unittest.TestCase):
    def test_parse_id(self):
        data = bytes.fromhex(SOME_SHORT)
        offset = 0
        id, offset = TAG.parse_id(data, offset)

        self.assertEqual(offset, 1)
        self.assertEqual(id, 2)

    def test_parse_name(self):
        data = bytes.fromhex(SOME_SHORT)
        offset = 1
        name, offset = TAG.parse_name(data, offset)

        self.assertEqual(name, "shortTest")
        self.assertEqual(offset, 1+2+len(name))

    def test_Short(self):
        reader = AtomReader(ShortTrait)
        data = bytes.fromhex(SOME_SHORT)
        offset = 0
        id, offset = TAG.parse_id(data, offset)
        name, offset = TAG.parse_name(data, offset)
        item, offset = reader.make_from_payload(data, offset, parent=None)

        self.assertEqual(data[offset:], b"")
        self.assertEqual(id, 2)
        self.assertEqual(item._payload, bytes.fromhex("7F FF"))

class TestParseTags(unittest.TestCase):
    def test_parse_end(self):
        t, name, offset = TAG.parse(bytes.fromhex("00"), 0)
        self.assertIsInstance(t, End)
        self.assertIs(t._trait, EndTrait)

    def test_parse_short(self):
        t,name, offset = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertIsInstance(t, AtomProxy)
        self.assertIs(t._trait, ShortTrait)
        self.assertEqual(name, "shortTest")
        self.assertEqual(bytes(t._payload), bytes.fromhex("7F FF"))

class TestParseFiles(unittest.TestCase):
    def test_parse_level(self):
        """ It should load uncompressed NBT files
        """
        t = TAG.parse_file("test/data/level.dat")
        self.assertIsInstance(t, CompoundNode)

    def test_parse_server(self):
        """ It should load uncompressed NBT files
        """
        t = TAG.parse_file("test/data/servers.dat")
        self.assertIsInstance(t, CompoundNode)

class TestListTag(unittest.TestCase):
    def test_parse_list(self):
        data = bytes.fromhex(SOME_LIST + "FF")
        nbt, name, offset = TAG.parse(data, 0)
        self.assertEqual(data[offset:], b"\xFF")
        self.assertIsInstance(nbt, ListNode)
        self.assertEqual(len(nbt), 4)
        self.assertEqual(nbt[0], 0)
        self.assertEqual(nbt[1], 1)
        self.assertEqual(nbt[2], 2)
        self.assertEqual(nbt[3], 3)
        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4], 4)

    def test_set_item(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        val, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)

        self.assertIsNot(nbt[0], val)
        self.assertIsNotNone(nbt._payload)

        nbt[0] = val
        self.assertEqual(nbt[0], val.value())
        self.assertIsNone(nbt._payload)

    def test_append(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        val, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)

        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4], 4)
        self.assertIsNotNone(nbt._payload)

        nbt.append(val)

        self.assertEqual(nbt[4], val)
        self.assertIsNone(nbt._payload)

    def test_del_item(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        self.assertEqual(len(nbt), 4)
        self.assertEqual(nbt[0], 0)
        self.assertEqual(nbt[1], 1)
        self.assertEqual(nbt[2], 2)
        self.assertEqual(nbt[3], 3)
        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4], 4)

        del nbt[1]
        
        self.assertIsNone(nbt._payload)
        self.assertEqual(len(nbt), 3)
        self.assertEqual(nbt[0], 0)
        self.assertEqual(nbt[1], 2)
        self.assertEqual(nbt[2], 3)
        with self.assertRaises(IndexError):
          self.assertEqual(nbt[3], 4)

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
        self.assertEqual(t.shortTest, 32767)

    def test_get_value(self):
        t, _, _ = TAG.parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertEqual(t, 32767)

    def test_nested_compound(self):
        t, name, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(name, 'Data')
        child = t._items['Comp']

    def test_path(self):
        t, *_ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(t.Comp.shortTest, 32767)

    def test_del_item(self):
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(len(nbt.Comp), 2)
        self.assertEqual(nbt.Comp['byteTest'], 127)
        self.assertEqual(nbt.Comp['shortTest'], 32767)

        del nbt.Comp.shortTest
        
        self.assertIsNone(nbt._payload)
        self.assertEqual(len(nbt.Comp), 1)
        self.assertEqual(nbt.Comp['byteTest'], 127)
        with self.assertRaises(KeyError):
          self.assertEqual(nbt.Comp['shortTest'], 32767)

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

    def test_walk_compound(self):
        t, name, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
        self.assertEqual(set(name for name, *_ in t.walk()), set(('', '.Comp', '.Comp.shortTest', '.Comp.byteTest', '.shortTest')))

    # walk is now implemented with a Visitor
    # def test_visit_compound(self):
    #     t, name, _ = TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND), 0)
    #     self.assertSequenceEqual(list(name for name in t.visit()), ('', '.Comp', '.Comp.shortTest', '.Comp.byteTest', '.shortTest'))

    def test_walk_list(self):
        t, name, _ = TAG.parse(bytes.fromhex(SOME_LIST), 0)
        self.assertSequenceEqual([name for name, *_ in t.walk()], ['', '.0', '.1', '.2', '.3'])

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
        child1.invalidate()

        # print(t)
        # print(child1)
        # print(child2)
        # print(data)

        # Immutable value below the invalidated composite should
        # stay valid
        self.assertIsNotNone(data._payload)
        self.assertIsNotNone(child2._payload)

        # composite in the ancestors chain should be invalidated
        self.assertIsNone(child1._payload)
        self.assertIsNone(t._payload)

class TestSetValue(unittest.TestCase):
    def test_set_value_compound(self):
        """ Compound items can be updated
        """
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_COMPOUND), 0)
        val, *_ = TAG.parse(bytes.fromhex(SOME_SHORT), 0)

        nbt.x = val
        self.assertIn("x", nbt.keys())
        self.assertEqual(val, nbt.x)

    def test_copy(self):
        """ Items can be copied between compounds
        """
        nbt, *_ = TAG.parse(bytes.fromhex(SOME_COMPOUND), 0)
        other, *_ = TAG.parse(bytes.fromhex(EMPTY_COMPOUND), 0)

        other.x = nbt.shortTest
        self.assertIn("x", other.keys())
        self.assertIs(nbt.shortTest, other.x)

import io
class TestWrite(unittest.TestCase):
    def test_write_atom(self):
        """ It should write back atomic values
        """
        data = bytes.fromhex(SOME_SHORT)
        nbt, name, _ = TAG.parse(data, 0)

        output = io.BytesIO()
        nbt.write(output, name)

        self.assertEqual(output.getbuffer(), data)

    def test_write_compound(self):
        """ It should write back compound values
        """
        data = bytes.fromhex(SOME_NESTED_COMPOUND)
        nbt, name, _ = TAG.parse(data, 0)

        output = io.BytesIO()
        nbt.write(output, name)

        self.assertEqual(output.getbuffer(), data)

    def test_write_change(self):
        """ It should write changes
        """
        data = bytes.fromhex(SOME_COMPOUND)
        nbt, name, _ = TAG.parse(data, 0)

        nbt.shortTest = 0x1234

        output = io.BytesIO()
        nbt.write(output, name)

        self.assertIn(b'\x02\x00\tshortTest\x124', bytes(output.getbuffer()))

    def test_write_copies(self):
        """ It should write items copied from other nbt
        """
        data = bytes.fromhex(SOME_COMPOUND)
        nbt, name, _ = TAG.parse(data, 0)

        nbt.otherShort = nbt.shortTest

        output = io.BytesIO()
        nbt.write(output, name)

        self.assertIn(b'\x02\x00\x09shortTest\x7F\xFF', bytes(output.getbuffer()))
        self.assertIn(b'\x02\x00\x0AotherShort\x7F\xFF', bytes(output.getbuffer()))

