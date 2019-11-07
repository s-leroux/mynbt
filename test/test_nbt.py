import unittest
import shutil
import os.path

from mynbt.nbt import *
from test.data.nbt import *
from pprint import pprint

FILE = {
  'level.dat': os.path.join('test','data','level.dat'),
  'copy.dat': os.path.join('test','tmp','copy.dat'),
}

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
        data = SOME_SHORT.BYTES
        offset = 0
        id, offset = parse_id(data, offset)

        self.assertEqual(offset, 1)
        self.assertEqual(id, 2)

    def test_parse_name(self):
        data = SOME_SHORT.BYTES
        offset = 1
        name, offset = parse_name(data, offset)

        self.assertEqual(name, "shortTest")
        self.assertEqual(offset, 1+2+len(name))

    def test_Short(self):
        reader = AtomReader(ShortTrait)
        data = SOME_SHORT.BYTES
        offset = 0
        id, offset = parse_id(data, offset)
        name, offset = parse_name(data, offset)
        item, offset = reader.make_from_payload(data, offset, parent=None)

        self.assertEqual(data[offset:], b"")
        self.assertEqual(id, 2)
        self.assertEqual(item._payload, bytes.fromhex("7F FF"))

class TestParseTags(unittest.TestCase):
    def test_parse_end(self):
        t, name, offset = parse(bytes.fromhex("00"), 0)
        self.assertIsInstance(t, End)
        self.assertIs(t._trait, EndTrait)

    def test_parse_short(self):
        t,name, offset = parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertIsInstance(t, AtomProxy)
        self.assertIs(t._trait, ShortTrait)
        self.assertEqual(name, "shortTest")
        self.assertEqual(bytes(t._payload), bytes.fromhex("7F FF"))

class TestParseFiles(unittest.TestCase):
    def test_parse_level(self):
        """ It should load uncompressed NBT files
        """
        t = parse_file(FILE['level.dat'])
        self.assertIsInstance(t, CompoundNode)

    def test_parse_server(self):
        """ It should load uncompressed NBT files
        """
        t = parse_file("test/data/servers.dat")
        self.assertIsInstance(t, CompoundNode)

class TestListTag(unittest.TestCase):
    def test_parse_list(self):
        data = bytes.fromhex(SOME_LIST.HEX + "FF")
        nbt, name, offset = parse(data, 0)
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
        nbt, *_ = parse(SOME_LIST.BYTES, 0)
        val, *_ = parse(SOME_SHORT.BYTES, 0)

        self.assertIsNot(nbt[0], val)
        self.assertIsNotNone(nbt._payload)

        nbt[0] = val
        self.assertEqual(nbt[0], val.value())
        self.assertIsNone(nbt._payload)

    def test_append(self):
        nbt, *_ = parse(SOME_LIST.BYTES, 0)
        val, *_ = parse(SOME_SHORT.BYTES, 0)

        with self.assertRaises(IndexError):
          self.assertEqual(nbt[4], 4)
        self.assertIsNotNone(nbt._payload)

        nbt.append(val)

        self.assertEqual(nbt[4], val)
        self.assertIsNone(nbt._payload)

    def test_del_item(self):
        TEST_DATA=LIST_FRAME(SHORT, [0,1,2,3])
        nbt, *_ = parse(TEST_DATA.BYTES)
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
        t = parse_file(FILE['level.dat'])
        self.assertEqual(list(t.keys()), ['Data'])

    def test_get_attr(self):
        t = parse_file(FILE['level.dat'])
        item = t.Data
        self.assertIn('DataPacks', list(item.keys()))
        self.assertIn('GameRules', list(item.keys()))

    def test_get_item(self):
        t = parse_file(FILE['level.dat'])
        item = t['Data']
        self.assertIn('DataPacks', list(item.keys()))
        self.assertIn('GameRules', list(item.keys()))

    def test_get_value_in_compount(self):
        t, _, _ = parse(SOME_COMPOUND.BYTES, 0)
        self.assertEqual(t.shortTest, 32767)

    def test_get_value(self):
        t, _, _ = parse(bytes.fromhex("02  00 09  73 68 6F 72 74 54 65 73 74  7F FF"), 0)
        self.assertEqual(t, 32767)

    def test_nested_compound(self):
        t, name, _ = parse(SOME_NESTED_COMPOUND.BYTES, 0)
        self.assertEqual(name, 'Data')
        child = t['Comp']

    def test_path(self):
        t, *_ = parse(SOME_NESTED_COMPOUND.BYTES, 0)
        self.assertEqual(t.Comp.shortTest, 32767)

    def test_del_item(self):
        nbt, *_ = parse(SOME_NESTED_COMPOUND.BYTES, 0)
        self.assertEqual(len(nbt.Comp), 2)
        self.assertEqual(nbt.Comp['byteTest'], 127)
        self.assertEqual(nbt.Comp['shortTest'], 32767)

        del nbt.Comp.shortTest
        
        self.assertIsNone(nbt._payload)
        self.assertEqual(len(nbt.Comp), 1)
        self.assertEqual(nbt.Comp['byteTest'], 127)
        with self.assertRaises(KeyError):
          self.assertEqual(nbt.Comp['shortTest'], 32767)

class TestArray(unittest.TestCase):
    def _test_array(self, frame, mod):
        data = [i%mod for i in range(10000)]
        frame = frame(data, name="")
        a, *_ = parse(frame)
        a = a.value() # Force data unpacking
        a._payload = None # clear cache
      
        for i,j in zip(a, data):
            self.assertEqual(i&(mod-1),j) # unsigned comparaison

        output = io.BytesIO()
        a.write_to(output)
        self.assertEqual(bytes(output.getbuffer()), bytes(frame))

    def test_byte_array(self):
        self._test_array(BYTE_ARRAY_FRAME, 1<<8)

    def test_int_array(self):
        self._test_array(INT_ARRAY_FRAME, 1<<32)

    def test_long_array(self):
        self._test_array(LONG_ARRAY_FRAME, 1<<64)

class TestBitPack(unittest.TestCase):
    def test_1(self):
        frame = LONG_ARRAY_FRAME([0x12345678FFF0A987]*100, name="")
        arr, *_ = parse(frame)
        arr = arr.value()

        bp = arr.toBitPack(4)

        for word in bp[0::16]:
            self.assertEqual(word, 0x07)
        for word in bp[1::16]:
            self.assertEqual(word, 0x08)
        for word in bp[2::16]:
            self.assertEqual(word, 0x09)
        for word in bp[3::16]:
            self.assertEqual(word, 0x0A)
        for word in bp[4::16]:
            self.assertEqual(word, 0x00)
        for word in bp[5::16]:
            self.assertEqual(word, 0x0F)
        for word in bp[6::16]:
            self.assertEqual(word, 0x0F)
        for word in bp[7::16]:
            self.assertEqual(word, 0x0F)

    def test_2(self):
        frame = LONG_ARRAY_FRAME([0x12345678FFF0A987]*100, name="")
        arr, *_ = parse(frame)
        arr = arr.value()

        bp = arr.toBitPack(4)

        output = io.BytesIO()
        bp.write_to(output)
        result = bytes(output.getbuffer())

        self.assertEqual(frame, result)

class TestExport(unittest.TestCase):
    CASES = (
      dict(dump=SOME_SHORT.BYTES, value=32767, extended={'type': 'TAG_Short', 'value': 32767}),
      dict(dump=SOME_COMPOUND.BYTES, value=dict(shortTest=32767, byteTest=127), extended=dict(type='TAG_Compound', value={'shortTest': {'type': 'TAG_Short', 'value': 32767}, 'byteTest':{'type':'TAG_Byte', 'value':127}})),
    )

    def _test_export(self, data, expected):
          t, *_ = parse(data.BYTES)

          x = t.export()
          self.assertEqual(x, expected)

          x = t.export(compact=True)
          self.assertEqual(x, expected)
    
    def _test_export_frame(self, frame, value):
          self._test_export(frame(value), value)

    def test_export_byte(self):
        self._test_export_frame(BYTE_FRAME, 127)

    def test_export_short(self):
        self._test_export_frame(SHORT_FRAME, 32767)

    def test_export_int(self):
        self._test_export_frame(INT_FRAME, 32767)

    def test_export_long(self):
        self._test_export_frame(LONG_FRAME, 32767)

    def test_export_long(self):
        self._test_export_frame(LONG_FRAME, 32767)

    def test_export_string(self):
        self._test_export_frame(STRING_FRAME, "Some String")

    def test_export_byte_array(self):
        self._test_export_frame(BYTE_ARRAY_FRAME, [1,2,3,4,5,6,7])

    def test_export_int_array(self):
        self._test_export_frame(INT_ARRAY_FRAME, [1,2,3,4,5,6,7])

    # There is currently no TAG_ShortArray
    # def test_export_short_array(self):
    #     self._test_export_frame(SHORT_ARRAY_FRAME, [1,2,3,4,5,6,7])

    def test_export_long_array(self):
        self._test_export_frame(LONG_ARRAY_FRAME, [1,2,3,4,5,6,7])

    def test_export_compound(self):
        data = COMPOUND_FRAME(
            SHORT_FRAME(123, name="short"),
            STRING_FRAME("abc", name="string"),
        )

        expected = dict(
            short=123,
            string="abc",
        )

        self._test_export(data, expected)

    def test_walk_compound(self):
        t, name, _ = parse(SOME_NESTED_COMPOUND.BYTES, 0)
        self.assertEqual(set(name for name, *_ in t.walk()), set(('', '.Comp', '.Comp.shortTest', '.Comp.byteTest', '.shortTest')))

    # walk is now implemented with a Visitor
    # def test_visit_compound(self):
    #     t, name, _ = TAG.parse(SOME_NESTED_COMPOUND.BYTES, 0)
    #     self.assertSequenceEqual(list(name for name in t.visit()), ('', '.Comp', '.Comp.shortTest', '.Comp.byteTest', '.shortTest'))

    def test_walk_list(self):
        t, name, _ = parse(SOME_LIST.BYTES, 0)
        self.assertSequenceEqual([name for name, *_ in t.walk()], ['', '.0', '.1', '.2', '.3'])

import gzip
class TestCache(unittest.TestCase):
    def test_compound_cache(self):
        with gzip.open(FILE['level.dat'], "rb") as f:
          data = f.read()
          t, _, offset = parse(data, 0)

        self.assertEqual(bytes(t._payload), data[3:])

    def test_parent_tracking(self):
        """ Nested elements shoud track their parent as weak links
        """
        t, *_ = parse(SOME_NESTED_COMPOUND.BYTES, 0)
        child = t['Comp']
        data = t['shortTest']

        self.assertEqual([*child._parents], [t])
        del t
        self.assertEqual([*child._parents], [])

    def test_invalidate(self):
        """ Invalidate should invalidate the whole ancestors chain
        """
        t, *_ = parse(SOME_NESTED_COMPOUND.BYTES, 0)
        child1 = t['Comp']
        child2 = t['shortTest']
        data = child1['shortTest']
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

class TestCycleDetection(unittest.TestCase):
    DATA = COMPOUND_FRAME(
        WITH_NAME("d1", COMPOUND_FRAME)(
          SHORT_FRAME(123, "a"),
        ),
        WITH_NAME("d2", COMPOUND_FRAME)(
            WITH_NAME("d21", COMPOUND_FRAME)(
              INT_FRAME(456, "b"),
            ),
        ),
    )

    def setUp(self):
        nbt, *_ = parse(self.DATA)
        self.root = nbt
        self.d1 = nbt.d1
        self.d2 = nbt.d2
        self.d21 = nbt.d2.d21

    def test_1(self):
        """ A node should be detected as its own ancestor
        """
        self.assertTrue(self.root.has_ancestor(self.root))
        self.assertTrue(self.d1.has_ancestor(self.d1))

    def test_2(self):
        """ A parent should be detected as an ancestor
        """
        self.assertTrue(self.d1.has_ancestor(self.root))
        self.assertTrue(self.d21.has_ancestor(self.d2))

    def test_3(self):
        """ A grand-parent should be detected as an ancestor
        """
        self.assertTrue(self.d21.has_ancestor(self.root))

    def test_4(self):
        """ Ancestor detection should work on DAG
        """
        self.d11 = self.d1.d11 = self.d21
        self.assertIs(self.d11, self.d21)
        self.assertTrue(self.d11.has_ancestor(self.d2))
        self.assertTrue(self.d11.has_ancestor(self.d1))

    def test_5(self):
        """ Cycle detection should raise an exception
        """
        with self.assertRaises(CircularReferenceError):
            self.d21.d211 = self.root

class TestSetValue(unittest.TestCase):
    def test_set_value_compound(self):
        """ Compound items can be updated
        """
        nbt, *_ = parse(SOME_COMPOUND.BYTES, 0)
        val, *_ = parse(SOME_SHORT.BYTES, 0)

        nbt.x = val
        self.assertIn("x", nbt.keys())
        self.assertEqual(val, nbt.x)

    def test_copy(self):
        """ Items can be copied between compounds
        """
        nbt, *_ = parse(SOME_COMPOUND.BYTES, 0)
        other, *_ = parse(EMPTY_COMPOUND.BYTES, 0)

        other.x = nbt.shortTest
        self.assertIn("x", other.keys())
        self.assertIs(nbt.shortTest, other.x)

import io
class TestWrite(unittest.TestCase):
    def test_write_atom(self):
        """ It should write back atomic values
        """
        data = SOME_SHORT.BYTES
        nbt, name, _ = parse(data, 0)

        output = io.BytesIO()
        nbt.write_to(output, name)

        self.assertEqual(output.getbuffer(), data)

    def test_write_compound(self):
        """ It should write back compound values
        """
        data = SOME_NESTED_COMPOUND.BYTES
        nbt, name, _ = parse(data, 0)

        output = io.BytesIO()
        nbt.write_to(output, name)

        self.assertEqual(output.getbuffer(), data)

    def test_write_change(self):
        """ It should write changes
        """
        data = SOME_COMPOUND.BYTES
        nbt, name, _ = parse(data, 0)

        nbt.shortTest = 0x1234

        output = io.BytesIO()
        nbt.write_to(output, name)

        self.assertIn(b'\x02\x00\tshortTest\x124', bytes(output.getbuffer()))

    def test_write_copies(self):
        """ It should write items copied from other nbt
        """
        data = SOME_COMPOUND.BYTES
        nbt, name, _ = parse(data, 0)
        nbt.otherShort = nbt.shortTest

        output = io.BytesIO()
        nbt.write_to(output, name)

        self.assertIn(b'\x02\x00\x09shortTest\x7F\xFF', bytes(output.getbuffer()))
        self.assertIn(b'\x02\x00\x0AotherShort\x7F\xFF', bytes(output.getbuffer()))

class Versioning(unittest.TestCase):
    def test_verion(self):
        """ After parsing, nodes should be at version 0
        """
        with gzip.open(FILE['level.dat'], "rb") as f:
          data = f.read()
          t, _, offset = parse(data, 0)

        self.assertEqual(t._version, 0)

    def test_version_update(self):
        """ Nested elements shoud track their parent as weak links
        """
        t, *_ = parse(COMPOUND_FRAME(
            WITH_NAME("Data", COMPOUND_FRAME)(
              SHORT_FRAME(123, "a"),
              INT_FRAME(456, "b"),
            )
        ))

        self.assertEqual(t._version, 0)

        del t.Data.b
        v1 = t._version
        self.assertGreater(v1, 0)

        t.Data.a=789
        v2 = t._version
        self.assertGreater(v2, v1)

        t.Data.c=0
        v3 = t._version
        self.assertGreater(v3, v2)

class TestSave(unittest.TestCase):
    def setUp(self):
        shutil.copy(FILE['level.dat'],FILE['copy.dat'])

    def test_1(self):
        """ NBT tree parsed from file can be saved
            with their original name
        """
        nbt = parse_file(FILE['copy.dat'])
        self.assertNotEqual(nbt.Data.LevelName, 'copy')
        nbt.Data.LevelName='copy'
        nbt.save()

        nbt = parse_file(FILE['copy.dat'])
        self.assertEqual(nbt.Data.LevelName, 'copy')

    def test_2(self):
        """ NBT data from file act as a context manager to save changes
        """
        with parse_file(FILE['copy.dat']) as nbt:
            self.assertNotEqual(nbt.Data.LevelName, 'copy')
            nbt.Data.LevelName='copy'

        with parse_file(FILE['copy.dat']) as nbt:
            self.assertEqual(nbt.Data.LevelName, 'copy')

    def test_3(self):
        """ Non-modified files are not auto-saved
        """
        with open(FILE['copy.dat'], 'rb') as f:
            old_data = f.read()

        with parse_file(FILE['copy.dat']) as nbt:
            self.assertNotEqual(nbt.Data.LevelName, 'copy')

        with open(FILE['copy.dat'], 'rb') as f:
            new_data = f.read()

        self.assertEqual(old_data, new_data)

class TestClone(unittest.TestCase):
    DATA = COMPOUND_FRAME(
        WITH_NAME("data", COMPOUND_FRAME)(
          SHORT_FRAME(123, "value"),
        ),
    )

    def setUp(self):
        self.nbt, *_ = parse(self.DATA)

    def test_1(self):
        """ Compound can be cloned
        """
        clone = self.nbt.clone()

        self.assertIsNot(clone, self.nbt)
        self.assertIs(clone.data['value'], self.nbt.data['value'])

    def test_2(self):
        """ Changing a value in a clone does not change the original
        """
        clone = self.nbt.clone()
        clone.data['value'] = 456

        self.assertEqual(clone.data['value'], 456)
        self.assertEqual(self.nbt.data['value'], 123)
