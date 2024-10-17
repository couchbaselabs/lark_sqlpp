from lark import Lark
from lark_sqlpp.collection_extractor import CollectionExtractor
from lark_sqlpp.dml_checker import DmlChecker
from lark_sqlpp.ddl_checker import DdlChecker
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
grammar = open(dir_path + "/sqlpp.lark").read()
parser = Lark(grammar)

def parse_sqlpp(source):
    """
    Parses an sql++ script into an AST
    :param source: script to parse
    :return: generated AST
    """
    return parser.parse(source)

def extract_collections(parsed_tree):
    """
    Extracts all collections from parsed sqlpp syntax tree
    :param parsed_tree: an abstract syntax tree representing a parsed sqlpp query
    :return: list of collection references
    """
    extractor = CollectionExtractor(parsed_tree)
    return extractor.get_paths()

def modifies_data(parsed_tree):
    """
    Checks if the tree contains a data modification query
    :param parsed_tree:
    :return: True or False
    """
    return DmlChecker(parsed_tree).check()

def modifies_structure(parsed_tree):
    """
    Checks if the tree contains a structure modification query
    :param parsed_tree:
    :return: True or False
    """
    return DdlChecker(parsed_tree).check()