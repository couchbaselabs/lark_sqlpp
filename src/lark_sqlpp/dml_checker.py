from lark import Visitor, v_args

@v_args(tree=True)
class DmlChecker(Visitor):
    def __init__(self, tree):
        self.contains_dml = False
        self.visit(tree)
    def dml_statement(self, tree):
        self.contains_dml = True
        return tree
    def check(self):
        return self.contains_dml
