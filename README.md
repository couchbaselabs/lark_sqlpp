# Lark SQL++ grammar

Sql++ lark grammar implementation for python and (potentially) javascript.

## Usage in python

### Installing the package with pip:
```shell
pip install git+ssh://git@github.com/couchbaselabs/lark_sqlpp#egg=lark_sqlpp
```

### Example usage
```python
from lark_sqlpp import *

def main():
    # validate a query
    parse_sqlpp("SELECT 1")

    # extract collection paths
    collection_paths = extract_collections(parse_sqlpp("SELECT * FROM test"))

    # check if sqlpp script modifies data
    modifies_data(parse_sqlpp("UPDATE test SET x = y"))

    # check if sqlpp script modifies structure
    modifies_structure(parse_sqlpp("CREATE SCOPE test.scope"))
```
