from __future__ import annotations

import pytest

from app import utils


@pytest.mark.parametrize(
    "predicate, xs, expected",
    [
        (lambda x: x == " ", [*"hello world"], [*"helloworld"]),
        (lambda x: x == " ", [*"hello, friendly world"], [*"hello,friendly world"]),
        (lambda x: x == " ", [*"helloworld"], [*"helloworld"]),
        (lambda x: x == " ", [*""], [*""]),
    ],
)
def test_remove_first(predicate, xs, expected):
    assert utils.remove_first(predicate, xs) == None
    assert xs == expected
