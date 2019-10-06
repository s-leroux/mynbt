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
      self.slice = rslice(self.base)

    def test_nested(self):
      nested = self.slice[:]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, 0)
      self.assertEqual(nested.stop, len(self.base))

      nested = self.slice[1:-1]
      self.assertIs(nested.base, self.slice.base)
      self.assertEqual(nested.start, 1)
      self.assertEqual(nested.stop, len(self.base)-1)

    def test_nested_get_item(self):
      nested = self.slice[1:-1]
      nested = nested[1:-1]
      nested = nested[1:-1]
      self.assertEqual(nested[1], self.base[4])
      self.assertEqual(len(nested), len(self.base)-6)

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
