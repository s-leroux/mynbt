import unittest

from mynbt.utils import rslice

class TestRefSlices(unittest.TestCase):
    def test_slice_item_access(self):
        a = [*range(10)]
        b = rslice(a,1,4)
        self.assertEqual(b[0], 1)
        self.assertEqual(b[1], 2)
        self.assertEqual(b[2], 3)

    def test_slice_item_access_neg(self):
        a = [*range(10)]
        b = rslice(a,1,4)
        self.assertEqual(b[-1], 3)
        self.assertEqual(b[-2], 2)
        self.assertEqual(b[-3], 1)

    def test_slice_item_out_of_bounds(self):
        a = [*range(10)]
        b = rslice(a,1,4)

        for idx in -100,-4,3,100:
            with self.assertRaises(IndexError, msg=idx):
                b[idx]

    def test_slice_array(self):
        a = [*range(10)]
        b = rslice(a,1,4)
        self.assertEqual(b, a[1:4])

    def test_slice_array_reversed(self):
        a = [*range(10)]
        b = rslice(a,4,1)
        self.assertEqual(b, a[4:1])

    def test_slice_from_end(self):
        a = [*range(10)]
        b = rslice(a,-1,-4)
        self.assertEqual(b, a[-1:-4])

    def test_slice_from_end_reversed(self):
        a = [*range(10)]
        b = rslice(a,-4,-1)
        self.assertEqual(b, a[-4:-1])

    def test_slice_to_end(self):
        a = [*range(10)]
        b = rslice(a,1,None)
        self.assertEqual(b, a[1:])

    def test_slice_from_end(self):
        a = [*range(10)]
        b = rslice(a,-2,None)
        self.assertEqual(b, a[-2:])

    def test_slice_from_start(self):
        a = [*range(10)]
        b = rslice(a,None, 4)
        self.assertEqual(b, a[:4])

    def test_slice_copy(self):
        a = [*range(10)]
        b = rslice(a,None, None)
        self.assertEqual(b, a[:])

    def test_compatibility_with_byte_string(self):
        a = b"012345678"
        b = rslice(a,1,4)
        self.assertEqual(bytes(b), b"123")

class TestNestedSlices(unittest.TestCase):
    def setUp(self):
      self.base = b"ABCDEFGHIJK"
      self.slice = rslice(self.base, 1, len(self.base)-1)

    def test_nested_1(self):
      nested = self.slice[:]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.start)
      self.assertEqual(nested.stop, self.slice.stop)

    def test_nested_2(self):
      nested = self.slice[2:-2]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.start+2)
      self.assertEqual(nested.stop, self.slice.stop-2)

    def test_nested_3(self):
      nested = self.slice[2:]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.start+2)
      self.assertEqual(nested.stop, self.slice.stop)

    def test_nested_4(self):
      nested = self.slice[-2:]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.stop-2)
      self.assertEqual(nested.stop, self.slice.stop)

    def test_nested_5(self):
      nested = self.slice[:-2]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.start)
      self.assertEqual(nested.stop, self.slice.stop-2)

    def test_nested_6(self):
      """ nested slices shouldn't escape parent's boundaries
      """
      nested = self.slice[:100]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.start)
      self.assertEqual(nested.stop, self.slice.stop)

    def test_nested_7(self):
      """ nested slices shouldn't escape parent's boundaries
      """
      nested = self.slice[-100:]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.start)
      self.assertEqual(nested.stop, self.slice.stop)

    def test_nested_8(self):
      """ nested slices shouldn't escape parent's boundaries
      """
      nested = self.slice[100:]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, self.slice.stop)
      self.assertEqual(nested.stop, self.slice.stop)

    def test_nested_get_item(self):
      nested = self.slice[1:-1]
      nested = nested[1:-1]
      nested = nested[1:-1]
      self.assertEqual(nested[1], self.base[5])
      self.assertEqual(len(nested), len(self.base)-8)

class TestBytesSlice(unittest.TestCase):
    def test_bytes_slice(self):
      data = b"0123456"
      b = rslice(data)

      self.assertEqual(b[0], data[0])
      self.assertEqual(b[1], data[1])
      self.assertEqual(b[2], data[2])
      self.assertEqual(b[3], data[3])
      self.assertEqual(b[4], data[4])
      self.assertEqual(b[5], data[5])
      self.assertEqual(b[6], data[6])

    def test_bytes_slice_to_bytes(self):
      b = rslice(b"0123456")

      self.assertEqual(bytes(b), b"0123456")

class TestSliceMath(unittest.TestCase):
    def setUp(self):
      self.base = b"ABCDEFGHIJK"
      self.slice = rslice(self.base)

    def test_slice_add(self):
      a = self.slice[1:3]
      b = self.slice[3:6]
      c = a+b

      self.assertIs(c.base, self.slice.base)
      self.assertEqual(len(c), 5)
      self.assertEqual(c.start, a.start)
      self.assertEqual(c.stop, b.stop)
