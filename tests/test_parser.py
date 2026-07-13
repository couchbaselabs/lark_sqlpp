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