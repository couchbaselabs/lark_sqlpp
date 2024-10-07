from sqlpp_lark_couchbase import parse_sqlpp


def test_parser():
    f = open("tests/tests.sqlpp")
    print(parse_sqlpp(f.read()))

