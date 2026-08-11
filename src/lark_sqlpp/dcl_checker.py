from lark import Visitor, v_args

@v_args(tree=True)
class DclChecker(Visitor):
    def __init__(self, tree):
        self.contains_dcl = False
        self.visit(tree)
    def dcl_statement(self, tree):
        self.contains_dcl = True
        return tree
    def check(self):
        return self.contains_dcl
