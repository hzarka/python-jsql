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

