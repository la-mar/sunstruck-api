import numpy as np
import pandas as pd
import pytest

import util.iterables as it


@pytest.fixture
def queryable():
    yield {
        "slim": {
            "enabled": True,
            "exclude": [],
            "model": "ProdStat",
            "path": "/path/to/endpoint",
            "aliases": {"key": "value", "key2": "value2"},
            "tasks": [
                {
                    "name": "example_sync",
                    # "mode": "sync",
                    "cron": {"minute": "*/15"},
                    "options": None,
                },
                {
                    "name": "example_full",
                    # "mode": "full",
                    "cron": {"minute": 0, "hour": 0, "day_of_week": 0},
                    "options": None,
                },
            ],
        }
    }


def test_chunks():
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expected = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]
    result = [list(x) for x in it.chunks(values, n=2)]
    assert result == expected


def test_chunks_nested_iterables():
    values = [1, 2, 3, 4, [1, 2, 3, 4], [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]]
    expected = [
        [1, 2],
        [3, 4],
        [[1, 2, 3, 4], [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]],
    ]
    result = [list(x) for x in it.chunks(values, n=2)]
    assert result == expected


@pytest.mark.parametrize(
    "data,expected",
    [
        (1, [1]),
        ("heart of stone", ["heart of stone"]),
        ([1, 2, 3], [1, 2, 3]),
        ((1), [(1)]),
        (dict(), [{}]),
        ({1: 1, 2: 2, 3: 3}, [{1: 1, 2: 2, 3: 3}]),
        (set(), []),
        ({1, 2, 3}, [1, 2, 3]),
        (frozenset([1, 2, 3]), [1, 2, 3]),
        (frozenset(), []),
        (np.array([1, 2, 3]), [1, 2, 3]),
        (np.array([1]), [1]),
        (np.array([]), []),
        (pd.Series([1, 2, 3], dtype=int), [1, 2, 3]),
        (pd.Series([1], dtype=int), [1]),
        (pd.Series(dtype=int), []),
    ],
)
def test_ensure_list(data, expected):
    assert it.ensure_list(data) == expected


@pytest.mark.parametrize(
    "data,expected",
    [
        ([1, 2, 3], [1, 2, 3]),
        ([[[1]]], 1),
        ([[[1, 2, 3]]], [1, 2, 3]),
        ([[1, 2, 3]], [1, 2, 3]),
        ([{1: 2}], {1: 2}),
        ({1: 2}, {1: 2}),
        ({}, {}),
        (1, 1),
        ([[[1], 2]], [[1], 2]),
        ([], None),
        ([[]], None),
        ([{}], {}),
        (set(), None),
        ({1}, 1),
        ({1, 2, 3}, [1, 2, 3]),
        (frozenset([1, 2, 3]), [1, 2, 3]),
        (frozenset([1]), 1),
        (frozenset(), None),
        (np.array([1, 2, 3]), [1, 2, 3]),
        (np.array([1]), [1]),
        (np.array([]), None),
        (pd.Series([1, 2, 3], dtype=int), [1, 2, 3]),
        (pd.Series([1], dtype=int), 1),
        (pd.Series(dtype=int), None),
    ],
)
def test_reduce(data, expected):
    assert it.reduce(data) == expected


def test_make_hash_from_list():
    items = ["eat", "more", "creatine", 1, 2, 3]
    hash1 = it.make_hash(items)
    assert hash1 == it.make_hash(items)


def test_make_hash_from_simple_mapping():
    items = {"key": "value", "another_key": "another_value"}
    hash1 = it.make_hash(items)
    assert hash1 == it.make_hash(items)


def test_make_hash_from_complex_mapping(queryable):
    hash1 = it.make_hash(queryable)
    assert hash1 == it.make_hash(queryable)
