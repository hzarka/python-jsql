import pytest

import jsql


# Test SQL proxy factory
def test_sql_proxy_factory():
    def mock_execute_sql(engine, query, params):
        class ResultProxy:
            def keys(self):
                return ["engine", "query", "params"]

            def __iter__(self):
                return iter([[engine, query, params]])

        return ResultProxy()

    jsql.execute_sql = mock_execute_sql

    engine = object()
    query = "SELECT 1 FROM tbl {% if customer %}WHERE customer=:customer{% endif %}"
    params = {"customer": "abc"}
    ret = jsql.get_sql_proxy_factory(engine)(query, params).dict()
    assert ret["engine"] == engine
    assert ret["query"] == "SELECT 1 FROM tbl "
    assert ret["params"]["customer"] == "abc"


def test_get_sql_proxy():
    def mock_execute_sql(engine, query, params):
        class ResultProxy:
            def keys(self):
                return ["engine", "query", "params"]

            def __iter__(self):
                return iter([[engine, query, params]])

        return ResultProxy()

    jsql.execute_sql = mock_execute_sql

    engine = object()
    query = "SELECT 1 FROM tbl {% if customer %}WHERE customer=:customer{% endif %}"
    params = {"customer": "abc"}
    ret = jsql.get_sql_proxy(engine, query, params).dict()
    assert ret["engine"] == engine
    assert ret["query"] == "SELECT 1 FROM tbl "
    assert ret["params"]["customer"] == "abc"
