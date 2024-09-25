from __future__ import annotations

import pytest

from app import utils


@pytest.mark.parametrize(
    "s, expected",
    [
        ("   hello  there    \n\n\n\nworld\n\n", ["hello  there", "world"]),
        ("\n\n\n", []),
    ],
)
def test_splitlines_clean(s, expected):
    assert utils.splitlines_clean(s) == expected


@pytest.mark.parametrize(
    "s, expected",
    [
        (
            "Single apostrophe is preserved: Matthew O'Brien (mathematician)",
            "Single apostrophe is preserved Matthew O'Brien mathematician",
        ),
        ("UTF-8 紅樓夢!", "UTF8 紅樓夢"),
        ("1+1=2.", "112"),
    ],
)
def test_strip_to_alphanum(s, expected):
    assert utils.strip_to_alphanum(s) == expected
