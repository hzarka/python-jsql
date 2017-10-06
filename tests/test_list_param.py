import jsql
import pytest

def test_simple_list_param():
    ids = [1, '2', 3, '100']
    query, params = jsql.format_query_with_list_params('id IN :id_list', dict(id_list=ids))
    assert query == 'id IN (:id_list_0, :id_list_1, :id_list_2, :id_list_3)'
    assert params == {'id_list_0': 1, 'id_list_1': '2', 'id_list_2': 3, 'id_list_3': '100'}

def test_empty_list_param():
    ids = []
    query, params = jsql.format_query_with_list_params('id IN :id_list', dict(id_list=ids))
    assert query == 'id IN (null)'
    assert params == {}

def test_simple_tuple_list():
    tuples = [
        (123, 'val1'),
        (456, 'val2'),
    ]
    query, params = jsql.format_query_with_list_params('(key1, key2) IN :key_tuple_list', dict(key_tuple_list=tuples))
    assert query == '(key1, key2) IN ((:key_tuple_list_0_0, :key_tuple_list_0_1), (:key_tuple_list_1_0, :key_tuple_list_1_1))'
    assert params == {'key_tuple_list_0_0': 123, 'key_tuple_list_0_1': 'val1', 'key_tuple_list_1_0': 456, 'key_tuple_list_1_1': 'val2'}

