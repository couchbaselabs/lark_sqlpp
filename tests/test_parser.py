from exceptiongroup import catch
import pytest
from lark.exceptions import UnexpectedInput
from lark_sqlpp import parse_sqlpp, extract_collections, modifies_data, modifies_structure, modifies_privileges


def test_parser():
    f = open("tests/tests.sqlpp")
    parse_sqlpp(f.read())

def test_exract_collections():
    tree = parse_sqlpp("UPDATE `travel-sample`.`inventory`.`route` SET id = 321 WHERE id = 320")
    assert extract_collections(tree) == [['travel-sample', 'inventory', 'route']]

    tree = parse_sqlpp("SELECT * from bucket.scope.collection")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

    tree = parse_sqlpp("UPDATE bucket.scope.collection SET test = true")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

    tree = parse_sqlpp("SELECT * FROM bucket1.scope1.collection1 c1 JOIN bucket2.scope2.collection2 as c2 ON c1.id = c2.ref WHERE true")
    assert extract_collections(tree) == [['bucket1', 'scope1', 'collection1'], ['bucket2', 'scope2', 'collection2']]

    tree = parse_sqlpp("DELETE FROM collection where test = (select test from bucket.scope2.collection2)")
    assert extract_collections(tree) == [['collection'], ['bucket', 'scope2', 'collection2']]

def test_modifies_data():
    tree = parse_sqlpp("SELECT * from bucket.scope.collection")
    assert modifies_data(tree) == False

    tree = parse_sqlpp("DELETE from bucket.scope.collection")
    assert modifies_data(tree) == True

    tree = parse_sqlpp("UPDATE bucket.scope.collection set x = y")
    assert modifies_data(tree) == True

def test_modifies_structure():
    tree = parse_sqlpp("SELECT * from bucket.scope.collection")
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("DELETE from bucket.scope.collection")
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("CREATE SCOPE test.scope IF NOT EXISTS")
    assert modifies_structure(tree) == True

def test_modifies_privileges():
    tree = parse_sqlpp("SELECT * from bucket.scope.collection")
    assert modifies_privileges(tree) == False

    tree = parse_sqlpp("DELETE from bucket.scope.collection")
    assert modifies_privileges(tree) == False

    tree = parse_sqlpp("CREATE SCOPE test.scope IF NOT EXISTS")
    assert modifies_privileges(tree) == False

    tree = parse_sqlpp("GRANT bucket_full_access ON bucket TO alice")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert modifies_privileges(tree) == True

    tree = parse_sqlpp("REVOKE bucket_full_access ON bucket FROM alice")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert modifies_privileges(tree) == True

    tree = parse_sqlpp("GRANT query_select, query_insert TO alice, bob")
    assert modifies_privileges(tree) == True

    tree = parse_sqlpp("EXPLAIN GRANT bucket_full_access ON bucket TO alice")
    assert modifies_privileges(tree) == True

def test_explain():
    tree = parse_sqlpp("EXPLAIN SELECT * from bucket.scope.collection")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

def test_any_within():
    tree = parse_sqlpp("SELECT h.name, h.city, h.country FROM `travel-sample`.`inventory`.`hotel` h WHERE ANY v WITHIN h.reviews SATISFIES v = 5 END LIMIT 10;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert extract_collections(tree) == [['travel-sample', 'inventory', 'hotel']]

def test_any_in():
    tree = parse_sqlpp("SELECT any v in [1,2,3] satisfies v > 1 end as result;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_some_in():
    tree = parse_sqlpp("SELECT some v in [1,2,3] satisfies v > 1 end as result;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_where_within():
    tree = parse_sqlpp("SELECT * FROM hotel AS t WHERE \"Walton Wolf\" WITHIN t;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_where_exists():
    tree = parse_sqlpp("SELECT DISTINCT h.city FROM hotel AS h WHERE EXISTS h.reviews;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_prefix_not():
    for query in [
        "SELECT * FROM h WHERE NOT EXISTS (SELECT 1 FROM a)",
        "SELECT * FROM h WHERE h.a = 1 AND NOT EXISTS (SELECT 1 FROM a)",
        "SELECT * FROM h WHERE NOT EXISTS h.reviews",
        "SELECT * FROM h WHERE NOT h.free_parking",
        "SELECT * FROM h WHERE NOT (EXISTS (SELECT 1 FROM a))",
        "SELECT * FROM h WHERE NOT (h.x = 1)",
        "SELECT * FROM h WHERE h.a = 1 AND NOT h.b",
        "SELECT * FROM h WHERE h.a = 1 OR NOT h.b",
        "SELECT NOT h.a FROM h",
        # Also in tests.sqlpp, where a string literal currently swallows it unparsed.
        "SELECT meta(TMP).id FROM `ga_profiles` as TMP WHERE NOT EXISTS ("
        " SELECT RAW META(GA).id FROM `tempga_profiles` as GA WHERE META(GA).id = META(TMP).id)"
        " AND meta(TMP).cas <= 1699077903000000000;",
    ]:
        tree = parse_sqlpp(query)
        assert modifies_data(tree) == False
        assert modifies_structure(tree) == False
        assert modifies_privileges(tree) == False

    tree = parse_sqlpp("DELETE FROM h WHERE NOT EXISTS (SELECT 1 FROM a)")
    assert modifies_data(tree) == True

    tree = parse_sqlpp("UPDATE h SET x = 1 WHERE NOT EXISTS (SELECT 1 FROM a)")
    assert modifies_data(tree) == True

def test_infix_not_operators():
    for query in [
        "SELECT * FROM h WHERE h.city NOT IN ['a', 'b']",
        "SELECT * FROM h WHERE h.city NOT WITHIN ['a', 'b']",
        "SELECT * FROM h WHERE h.name NOT LIKE 'a%'",
        "SELECT * FROM h WHERE h.n NOT BETWEEN 1 AND 2",
        "SELECT * FROM h WHERE h.n IS NOT NULL",
        "SELECT * FROM h WHERE h.n IS NOT MISSING",
    ]:
        parse_sqlpp(query)

    tree = parse_sqlpp("SELECT * FROM h WHERE h.city NOT IN ['a', 'b']")
    assert len(list(tree.find_data("in_expr"))) == 1
    assert len(list(tree.find_data("not_expr"))) == 0

    tree = parse_sqlpp("SELECT * FROM h WHERE h.city NOT WITHIN ['a', 'b']")
    assert len(list(tree.find_data("within_expr"))) == 1
    assert len(list(tree.find_data("not_expr"))) == 0

def test_infix_not_rejected():
    for query in [
        "SELECT * FROM h WHERE h.a NOT h.b",
        "SELECT * FROM h WHERE h.a = 1 NOT h.b = 2",
    ]:
        with pytest.raises(UnexpectedInput):
            parse_sqlpp(query)

def test_unary_minus():
    for query in [
        "SELECT -1",
        "SELECT -1.5",
        "SELECT -h.x FROM h",
        "SELECT [-1, 2]",
        "SELECT 1 - -1",
        "SELECT * FROM h WHERE h.x > -1",
        "SELECT a.airportname, a.city, a.geo.lon FROM `travel-sample`.inventory.airport a"
        " WHERE a.geo.lon < -150 ORDER BY a.geo.lon LIMIT 5;",
        "SELECT h.name, h.public_likes[-1] AS last_like FROM `travel-sample`.inventory.hotel h"
        " WHERE ARRAY_LENGTH(h.public_likes) > 0 LIMIT 3;",
        'CREATE SEQUENCE seq4 IF NOT EXISTS WITH {"start": 10, "increment": -1, "min": 0};',
    ]:
        parse_sqlpp(query)

    tree = parse_sqlpp("SELECT 0 - 1")
    assert len(list(tree.find_data("arithmetic_term"))) == 1
    assert len(list(tree.find_data("neg_expr"))) == 0

def test_string_literals():
    def strings(tree):
        return [str(t.children[0]) for t in tree.find_data("double_quoted_string")] + \
               [str(t.children[0]) for t in tree.find_data("single_quoted_string")]

    tree = parse_sqlpp('SELECT * FROM h WHERE h.x = "a" AND h.y = "b"')
    assert sorted(strings(tree)) == ['"a"', '"b"']

    for query, expected in [
        ('SELECT "say \\"hi\\""', '"say \\"hi\\""'),
        ("SELECT 'it''s'", "'it''s'"),
        ("SELECT 'it\\'s'", "'it\\'s'"),
        ('SELECT "back\\\\slash"', '"back\\\\slash"'),
        ('SELECT "\\u00e9 \\n \\t"', '"\\u00e9 \\n \\t"'),
        ('SELECT "line1\nline2"', '"line1\nline2"'),
        ('SELECT "a; DELETE FROM b"', '"a; DELETE FROM b"'),
        ('SELECT "it\'s"', '"it\'s"'),
        ('SELECT \'say "hi"\'', '\'say "hi"\''),
        ('SELECT ""', '""'),
    ]:
        assert strings(parse_sqlpp(query)) == [expected]

    tree = parse_sqlpp('SELECT * FROM h WHERE h.x = "a; DELETE FROM b"')
    assert modifies_data(tree) == False

    with pytest.raises(UnexpectedInput):
        parse_sqlpp('SELECT "unterminated')

    # Couchbase: syntax error (3000), the string ends at the second quote.
    with pytest.raises(UnexpectedInput):
        parse_sqlpp('SELECT "say ""hi"""')

def test_string_cannot_hide_statements():
    # A string ends at its first unescaped quote, so text the grammar can't parse
    # fails the whole parse instead of being absorbed into one long string.
    for query in [
        'SELECT "a"; SELECT [ADD VECTOR HERE]; SELECT "b"',
        'SELECT * FROM h WHERE h.x = "a" AND h.y = [ADD VECTOR HERE] AND h.z = "b"',
        "SELECT 'a'; SELECT [ADD VECTOR HERE]; SELECT 'b'",
    ]:
        with pytest.raises(UnexpectedInput):
            parse_sqlpp(query)

    tree = parse_sqlpp('SELECT "a"; DELETE FROM b WHERE c = "d"; SELECT "e"')
    assert len(list(tree.find_data("statement"))) == 3
    assert modifies_data(tree) == True

    tree = parse_sqlpp('SELECT "a"; GRANT bucket_full_access ON bucket TO alice; SELECT "b"')
    assert modifies_privileges(tree) == True

def test_tests_file_parses_every_statement():
    # Guards against a string literal (or anything else) swallowing part of tests.sqlpp.
    # Every statement in the file ends with ";" at the end of a line.
    source = open("tests/tests.sqlpp").read()
    expected = sum(1 for line in source.splitlines() if line.rstrip().endswith(";"))
    tree = parse_sqlpp(source)
    assert len(list(tree.find_data("statement"))) == expected

def test_slice_expr():
    tree = parse_sqlpp("SELECT h.name, h.public_likes[0:2] AS top_likes FROM hotel AS h WHERE h.public_likes IS NOT MISSING LIMIT 5;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_subquery_paths():
    tree = parse_sqlpp("SELECT name, (SELECT RAW AVG(s.ratings.Overall) FROM t.reviews AS s)[0] AS avg_rating FROM `travel-sample`.inventory.hotel AS t ORDER BY avg_rating DESC LIMIT 3;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_tcl_statements():
    tree = parse_sqlpp("BEGIN TRANSACTION")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("START WORK")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SAVEPOINT s1")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("ROLLBACK TRANSACTION TO SAVEPOINT s1")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("ROLLBACK")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("COMMIT")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("COMMIT TRANSACTION")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("BEGIN TRANSACTION; SAVEPOINT s1; ROLLBACK TRANSACTION TO SAVEPOINT s1; COMMIT;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
def test_window_frame_clause():
    tree = parse_sqlpp("SELECT LAST_VALUE(r.distance) OVER (win ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS longest_distance FROM route r WINDOW win AS (ORDER BY r.id);")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS UNBOUNDED PRECEDING) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS CURRENT ROW) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS 3 PRECEDING) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y RANGE BETWEEN 1 PRECEDING AND 1 FOLLOWING EXCLUDE CURRENT ROW) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y GROUPS BETWEEN 2 PRECEDING AND 2 FOLLOWING) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING EXCLUDE NO OTHERS) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT SUM(x) OVER (ORDER BY y ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING EXCLUDE TIES) FROM foo;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_line_comment():
    tree = parse_sqlpp("-- top of file comment\nSELECT * FROM bucket.scope.collection")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

    tree = parse_sqlpp("SELECT * FROM bucket.scope.collection -- trailing comment")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

def test_block_comment():
    tree = parse_sqlpp("SELECT /* note */ * FROM bucket.scope.collection")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

    tree = parse_sqlpp("SELECT * /* spans\nmultiple\nlines */ FROM bucket.scope.collection")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

    tree = parse_sqlpp("SELECT * FROM bucket.scope.collection /**/")
    assert extract_collections(tree) == [['bucket', 'scope', 'collection']]

def test_array_transform_expr():
    tree = parse_sqlpp("SELECT ARRAY v FOR v IN schedule WHEN v.day = 5 END AS fri_flights FROM route WHERE airline = \"KL\";")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert extract_collections(tree) == [['route']]

    tree = parse_sqlpp("SELECT ARRAY v FOR v IN [1,2,3] END AS result;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_first_transform_expr():
    tree = parse_sqlpp("SELECT FIRST v FOR v IN schedule WHEN v.utc > \"19:00\" END AS first_flight FROM route;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert extract_collections(tree) == [['route']]

def test_object_transform_expr():
    tree = parse_sqlpp("SELECT OBJECT \"num_\" || TOSTRING(i):v FOR i:v IN schedule WHEN v.day = 5 END AS fri_flights FROM route;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False
    assert extract_collections(tree) == [['route']]

def test_index_with_array_expr():
    tree = parse_sqlpp("CREATE INDEX idx ON route(DISTINCT ARRAY v FOR v IN schedule END);")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == True

def test_sequence_value_expr():
    tree = parse_sqlpp("SELECT NEXT VALUE FOR ordNum;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT NEXTVAL FOR ordNum;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT PREVIOUS VALUE FOR ordNum;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT PREV VALUE FOR ordNum;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT PREVVAL FOR ordNum;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("SELECT PREV VALUE FOR bucket.scope.ordNum;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

    tree = parse_sqlpp("INSERT INTO bookings VALUES (UUID(), {\"num\": NEXT VALUE FOR ordNum, \"user\": 0});")
    assert modifies_data(tree) == True
    assert modifies_structure(tree) == False

