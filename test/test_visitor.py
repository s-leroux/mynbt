import unittest

import mynbt.nbt as nbt
from mynbt.visitor import *
from test.data.samples import *

class TestSmartVisitor(unittest.TestCase):
    def test_1(self):
        """ Smart visitor should dispatch to the most specialized method
        """
        tree, *_ = nbt.TAG.parse(bytes.fromhex(SOME_NESTED_COMPOUND))
        print(list(tree.visit(Exporter())))
