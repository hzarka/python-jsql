import pytest

import jsql


class FakeResult:
    def __init__(self, keys, rows):
        self._keys = keys
        self._rows = rows

    def keys(self):
        return self._keys

    def __iter__(self):
        return iter(self._rows)


example = FakeResult(
    ["id", "name"],
    [
        (1, "A"),
        (2, "B"),
        (3, "C"),
    ],
)

empty_example = FakeResult(["id", "name"], [])


def test_dict():
    res = jsql.SqlProxy(example)
    assert res.dict() == {"id": 1, "name": "A"}


def test_empty_dict():
    res = jsql.SqlProxy(empty_example)
    assert res.dict() is None


def test_dicts():
    res = jsql.SqlProxy(example)
    assert res.dicts() == [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
        {"id": 3, "name": "C"},
    ]


def test_kv_map():
    res = jsql.SqlProxy(example)
    assert res.kv_map() == {
        1: "A",
        2: "B",
        3: "C",
    }


def test_pk_map():
    res = jsql.SqlProxy(example)
    assert res.pk_map() == {
        1: {"id": 1, "name": "A"},
        2: {"id": 2, "name": "B"},
        3: {"id": 3, "name": "C"},
    }


def test_scalars():
    res = jsql.SqlProxy(example)
    assert res.scalars() == [1, 2, 3]


def test_scalar_set():
    res = jsql.SqlProxy(example)
    assert res.scalar_set() == {1, 2, 3}
