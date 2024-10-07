# Lark SQL++ grammar

Sql++ lark grammar implementation for python and (potentially) javascript.

## Usage in python

### Installing the package with pip:
```shell
pip install git+ssh://git@github.com/couchbaselabs/lark_sqlpp#egg=lark_sqlpp
```

### Example usage
```python
from sqlpp_lark import parse_sqlpp

def main():
    parse_sqlpp("SELECT 1")
```