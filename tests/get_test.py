from typing import Any, NamedTuple

import pytest

from filterpath import get


class SomeNamedTuple(NamedTuple):
    a: Any
    b: Any


class Object:
    def __init__(self, **attrs):
        for key, value in attrs.items():
            setattr(self, key, value)


@pytest.mark.parametrize(
    ("obj", "args", "expected"),
    [
        ({"one": {"two": {"three": 4}}}, ("one.two",), {"three": 4}),
        ({"one": {"two": {"three": 4}}}, ("one.two.three",), 4),
        ({"one": {"two": {"three": 4}}}, ("one.four",), None),
        ({"one": {"two": {"three": 4}}}, ("one.four.three", []), []),
        ({"one": {"two": {"three": 4}}}, ("one.four.three",), None),
        ({"one": {"two": {"three": [{"a": 1}]}}}, ("one.four.three.0.a",), None),
        ({"one": {"two": {"three": 4}}}, ("one.four.three", 2), 2),
        ({"one": {"two": {"three": 4}}}, ("five",), None),
        ({"one": ["two", {"three": [4, 5]}]}, ("one.1.three.1",), 5),
        ({"one": ["two", {"three": [4, 5]}]}, ("one.1.three",), [4, 5]),
        (["one", {"two": {"three": [4, 5]}}], ("1.two.three.0",), 4),
        (["one", {"two": {"three": [4, [{"four": [5]}]]}}], ("1.two.three.1.0.four.0",), 5),
        (["one", {"two": {"three[1]": [4, [{"four": [5]}]]}}], ("1.two.three[1].0",), 4),
        (["one", {"two": {"three": [4, [{"four": [5]}], 6]}}], ("1.two.three.-2.0.four.0",), 5),
        (range(50), ("42",), 42),
        (range(50), ("-1",), 49),
        ([[[[[[[[[[42]]]]]]]]]], ("0.0.0.0.0.0.0.0.0.0",), 42),
        ([range(50)], ("0.42",), 42),
        ({"a": [{"b": range(50)}]}, ("a.0.b.42",), 42),
        ({"one": ["hello", None]}, ("one.1.hello",), None),
        (SomeNamedTuple(1, 2), ("a",), 1),
        (SomeNamedTuple(1, 2), ("0",), 1),
        (SomeNamedTuple({"c": {"d": 1}}, 2), ("a.c.d",), 1),
        ({}, ("update",), None),
        ([], ("extend",), None),
        ({1: {"name": "John Doe"}}, ("1.name",), "John Doe"),
        (["1", 2, "c"], ("2.0",), None),
        (["1", 2, "c"], (".",), None),
        (["1", 2, "c"], ("0.",), "1"),
        ([{"": "a"}, 2, "c"], ("0.",), {"": "a"}),
        ([{"": "a"}, 2, "c"], ("0..",), "a"),
        ([{"": "a"}, 2, "c"], ("0...",), None),
        ({"": {"": "b"}}, (".",), {"": "b"}),
        ({"": {"": "b"}}, ("..",), "b"),
        ({"": {"": "b"}}, ("...",), None),
        (Object(), ("__name__",), None),
        (Object(), ("foo.__dict__",), None),
        (Object(), ("__len__",), None),
        ({}, ("__globals__",), None),
        ({}, ("__builtins__",), None),
        ([], ("__globals__",), None),
        ([], ("__builtins__",), None),
    ],
)
def test_get(obj, args, expected):
    assert get(obj, *args) == expected
