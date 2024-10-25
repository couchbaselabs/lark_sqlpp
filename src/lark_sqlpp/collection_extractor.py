from lark import Transformer, v_args, Token

@v_args(tree=True)
class CollectionExtractor(Transformer):
    def __init__(self, tree):
        self.paths = []
        self.transform(tree)
    def collection_ref(self, tree):
        if not isinstance(tree.children[0].children[0], Token):
            # this is an escaped identifier, ignore the backticks
            return tree.children[0].children[0].children[1].value
        return tree.children[0].children[0].value
    def scope_ref(self, tree):
        return self.collection_ref(tree)
    def bucket_ref(self, tree):
        return self.collection_ref(tree)
    def keyspace_path(self, tree):
        if len(tree.children) > 0 and type(tree.children[0]) is str:
            self.paths += [tree.children]
        return tree
    def keyspace_partial(self, tree):
        if len(tree.children) > 0 and type(tree.children[0]) is str:
            self.paths += [tree.children]
        return tree
    def path(self, tree):
        if len(tree.children) > 0 and type(tree.children[0]) is str:
            self.paths += [tree.children]
        return tree
    def get_paths(self):
        return self.paths
    def alias(self, tree):
        return None
    def select_statement(self, tree):
        return None