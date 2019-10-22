import unittest

import mynbt.nbt as nbt
from mynbt.visitor import *
from test.data.samples import *

class TestSmartVisitor(unittest.TestCase):
    def test_1(self):
        """ Smart visitor should dispatch to the most specialized method
        """
        tree, *_ = nbt.TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND))
        self.assertSequenceEqual(list(tree.visit(TraceSmartVisitor())), ['visitCompound', 'visitCompound', 'visitByte', 'visitShort', 'visitShort'])

class TestExporter(unittest.TestCase):
    def test_1(self):
        """ Exporter should export compound as nested dictionaries
        """
        tree, *_ = nbt.TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND))
        result, = tree.visit(Exporter())

        self.assertEqual(result,{'shortTest': 32767, 'Comp': {'byteTest': 127, 'shortTest': 32767}}) 

    def test_2(self):
        """ Exporter should export atomic values
        """
        tree, *_ = nbt.TAG.parse(bytes.fromhex(SOME_SHORT))
        result, = tree.visit(Exporter())

        self.assertEqual(result, 32767) 
