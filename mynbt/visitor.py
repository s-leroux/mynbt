""" Visitors for mynbt.Node.visit()
"""

class Visitor:
    """ The core visitor interface
        
        Default implementations do nothing
    """

    def enter(self, path, node):
        pass

    def leave(self, path, node):
        pass

class TraceVisitor(Visitor):
    def enter(self, path, node):
        return ("enter", path)

    def leave(self, path, node):
        return ("leave", path)

class SmartVisitor(Visitor):
    """ The _smart_ visitor will require node's cooperation
        to dispatch the enter and leave message to the
        right method depending the visited node.

        This is an implementation of the visitor pattern
        in accordance with the Go4 Design Pattern book.

        default implementations delegate to the vistor for
        the more generic node up until `visitNode`
    """
    class Action:
        def __init__(self, visitor, path, node):
            self._visitor = visitor
            self._path = path
            self._node = node

        def visitNode(self):
            pass
        def visitAtom(self):
            return self.visitNode()
        def visitInteger():
            return self.visitAtom()
        def visitFloat(self):
            return self.visitAtom()
        def visitString(self):
            return self.visitAtom()
        def visitArray(self):
            return self.visitNode()
        def visitList(self):
            return self.visitNode()
        def visitCompound(self):
            return self.visitNode()

    class Enter(Action):
        pass

    class Leave(Action):
        pass

    def enter(self, path, node):
        return node.accept(self.Enter(self, path, node))

    def leave(self, path, node):
        return node.accept(self.Leave(self, path, node))

class DSmartVisitor(SmartVisitor):
    class Enter(SmartVisitor.Enter):
        def visitNode(self):
            print('visitNode at '+self._path, type(self._node))
        def visitAtom(self):
            print('visitAtom at '+self._path, type(self._node))
        def visitInteger(self):
            print('visitInteger at '+self._path, type(self._node))
        def visitString(self):
            print('visitString at '+self._path, type(self._node))
        def visitArray(self):
            print('visitArray at '+self._path, type(self._node))
        def visitList(self):
            print('visitList at '+self._path, type(self._node))
        def visitCompound(self):
            print('visitCompound at '+self._path, type(self._node))

