import unittest

from mynbt.bitpack import *
from pprint import pprint
from array import array

from test.data.simplechunk import SECTION

class TestUtils(unittest.TestCase):
    def test_1(self):
        """ pos2idx and idx2pos should perform
            reverse operations
        """
        for t in ((0,0,0), (1,2,3), (15,15,15)):
            self.assertEqual(t, idx2pos(pos2idx(*t)))

    def test_2(self):
        """ pos2idx should convert X,Y,Z positions to indices
        """
        for k,v in {0:(0,0,0), 1+2*256+3*16: (1,2,3)}.items():
            self.assertEqual(k, pos2idx(*v))
            self.assertEqual(v, idx2pos(k))

class TestUnpack(unittest.TestCase):
    def test_1(self):
        """ Unpack should start decoding from the LSB
        """
        self.assertEqual(unpack(1, 8, [0xFE]).tolist(), [0,1,1,1,1,1,1,1])
        self.assertEqual(unpack(2, 8, [0xFE]).tolist(), [0b10,0b11,0b11,0b11])
        self.assertEqual(unpack(4, 8, [0xFE]).tolist(), [0b1110,0b1111])

    def test_2(self):
        s = array('Q', [1229782938247303441]*3)
        u = unpack(12, 64, s)
        r = pack(64, 12, u)
        self.assertEqual(s,r)
  
    def test_100(self):
        data = SECTION['BlockStates'][173:178]
        data = SECTION['BlockStates']
        palette = SECTION['Palette']
        n = len(palette)

        nbits = 4
        n //= 16
        while n:
            nbits += 1
            n //= 2

        print(nbits)
        print(data)

        result = unpack(nbits, 64, data)
        print(result)
        pprint([(idx2pos(n), palette[i]) for n, i in enumerate(result)])
