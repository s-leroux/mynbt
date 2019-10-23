""" Visitors for mynbt.Node.visit()
"""

class Visitor:
    """ The core visitor interface
        
        Default implementations do nothing
    """

    def enter(self, path, name, node):
        pass

    def leave(self, path, name, node):
        pass

    def close(self):
        """ Called by node.visit when the NBT tree has been entirely traversed.

            No other method of the visitor should be called after close() has
            been issued.
        """
        pass

class TraceVisitor(Visitor):
    def enter(self, path, name, node):
        return ("enter", path)

    def leave(self, path, name, node):
        return ("leave", path)

class SmartVisitor(Visitor):
    """ The _smart_ visitor will require node's cooperation
        to dispatch the enter and leave message to the
        right method depending the visited node.

        This is an implementation of the visitor pattern
        in accordance with the Go4 Design Pattern book.

        default implementations delegate to the vistor for
        a more generic function up until `visitNode`
    """
    class Action:
        def __init__(self, visitor, path, name, node):
            self._visitor = visitor
            self._path = path
            self._name = name
            self._node = node

        def visitNode(self):
            pass
        def visitAtom(self):
            return self.visitNode()
        def visitNumber(self):
            return self.visitAtom()
        def visitIntegral(self):
            return self.visitNumber()
        def visitByte(self):
            return self.visitIntegral()
        def visitShort(self):
            return self.visitIntegral()
        def visitInt(self):
            return self.visitIntegral()
        def visitLong(self):
            return self.visitIntegral()
        def visitFloatingPoint(self):
            return self.visitNumber()
        def visitFloat(self):
            return self.visitFloatingPoint()
        def visitDouble(self):
            return self.visitFloatingPoint()
        def visitString(self):
            return self.visitAtom()
        def visitComposite(self):
            return self.visitNode()
        def visitArray(self):
            return self.visitComposite()
        def visitByteArray(self):
            return self.visitArray()
        def visitShortArray(self):
            return self.visitArray()
        def visitLongArray(self):
            return self.visitArray()
        def visitList(self):
            return self.visitComposite()
        def visitCompound(self):
            return self.visitComposite()

    class Enter(Action):
        pass

    class Leave(Action):
        pass

    def enter(self, path, name, node):
        return node._trait.accept(self.Enter(self, path, name, node))

    def leave(self, path, name, node):
        return node._trait.accept(self.Leave(self, path, name, node))

class TraceSmartVisitor(SmartVisitor):
    class Enter(SmartVisitor.Enter):
        def __getattribute__(self, attr):
            if (attr.startswith('visit')):
                return lambda : attr

            return super().__getattribute__(attr)
        # def visitNode(self):
        #     print('visitNode at '+self._path, type(self._node))
        # def visitAtom(self):
        #     print('visitAtom at '+self._path, type(self._node))
        # def visitInteger(self):
        #     print('visitInteger at '+self._path, type(self._node))
        # def visitString(self):
        #     print('visitString at '+self._path, type(self._node))
        # def visitArray(self):
        #     print('visitArray at '+self._path, type(self._node))
        # def visitList(self):
        #     print('visitList at '+self._path, type(self._node))
        # def visitCompound(self):
        #     print('visitCompound at '+self._path, type(self._node))

class Exporter(SmartVisitor):
    @staticmethod
    def default_setter(name, node, top):
        def _(idx, value):
            raise "{name} cannot acccept {idx}"

        return (_, name, node, top)

    @staticmethod
    def dict_setter(name, node, top):
        dref = dict()
        def _(name, value):
            nonlocal dref
            dref[name] = value

        return (_, name, dref, top)

    @staticmethod
    def list_setter(name, node, top):
        lref = list()
        def _(idx, value):
            nonlocal lref
            lref.extend([None] * (1+idx - len(lref)))
            lref[idx] = value
            # print("added", lref, value, top)

        return (_, name, lref, top)

    def __init__(self):
        self._top = Exporter.dict_setter('', dict(), None)


    class Enter(SmartVisitor.Enter):
        def visitAtom(self):
            self._visitor._top = Exporter.default_setter(self._name, self._node, self._visitor._top)
        def visitCompound(self):
            self._visitor._top = Exporter.dict_setter(self._name, self._node, self._visitor._top)
        def visitArray(self):
            self._visitor._top = Exporter.list_setter(self._name, self._node, self._visitor._top)
    class Leave(SmartVisitor.Leave):
        def visitNode(self):
            _, name, item, self._visitor._top = self._visitor._top
            self._visitor._top[0](name, item)

    def close(self):
        assert self._top, str(self.__top)
        # print(self._top)
        return self._top[2]['']
