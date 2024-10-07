from lark import Lark
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
