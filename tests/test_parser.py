from exceptiongroup import catch
from lark_sqlpp import parse_sqlpp, extract_collections, modifies_data, modifies_structure


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

def test_slice_expr():
    tree = parse_sqlpp("SELECT h.name, h.public_likes[0:2] AS top_likes FROM hotel AS h WHERE h.public_likes IS NOT MISSING LIMIT 5;")
    assert modifies_data(tree) == False
    assert modifies_structure(tree) == False

def test_subquery_paths():
    tree = parse_sqlpp("SELECT name, (SELECT RAW AVG(s.ratings.Overall) FROM t.reviews AS s)[0] AS avg_rating FROM `travel-sample`.inventory.hotel AS t ORDER BY avg_rating DESC LIMIT 3;")
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
