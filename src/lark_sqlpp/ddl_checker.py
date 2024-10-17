from lark import Visitor, v_args

@v_args(tree=True)
class DdlChecker(Visitor):
    def __init__(self, tree):
        self.contains_ddl = False
        self.visit(tree)
    def ddl_statement(self, tree):
        self.contains_ddl = True
        return tree
    def check(self):
        return self.contains_ddl
