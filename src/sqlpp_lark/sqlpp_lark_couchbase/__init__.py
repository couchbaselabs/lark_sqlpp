from lark import Lark
import os


def parse_sqlpp(source):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    grammar = open(dir_path + "/sqlpp.lark").read()
    parser = Lark(grammar)
    return parser.parse(source)
