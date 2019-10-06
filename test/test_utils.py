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
