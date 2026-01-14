import pytest
from main import flatten_dict
class TestFlattenDict:
    def test_simple_dict(self):
        data = {"name": "John", "age": 30}
        result = flatten_dict(data)
        assert result == {"name" : "John", "age" : 30}

    def test_nested_dict(self):
        data = {
            "BillAddr" : {"City" : "NYC", "State" : "NY"},
            "Name" : "Customer"
        }
        expected = {
            "BillAddr_City" : "NYC",
            "BillAddr_State" : "NY",
            "Name" : "Customer"
        }
        assert flatten_dict(data) == expected

    def test_deep_nesting(self):
        data = {"Level1": {"Level2" : {"Level3" : "value"}}}
        result  = flatten_dict(data)
        assert result == {"Level1_Level2_Level3" : "value"}


