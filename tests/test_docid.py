from __future__ import annotations

import pytest

from app import docid
from fixture_requests import *


@pytest.mark.parametrize(
    "response, expected",
    [
        (MockResponse(200), True),
        (MockResponse(300), False),
        (MockResponse(101), False),
    ],
)
def test_ok_response(response, expected):
    assert docid.ok_response(response) == expected


def test_lookup_isbn(mocker, isbn_and_author_response):
    isbn_response, author_response, expected = isbn_and_author_response
    get = mocker.patch("requests.get")
    get.side_effect = [isbn_response, author_response]
    assert docid.lookup_isbn(expected.get("isbn10", {})) == expected


def test_lookup_doi(mocker, doi_response):
    response, expected = doi_response
    get = mocker.patch("requests.get")
    get.return_value = response
    assert docid.lookup_doi(expected.get("doi", {})) == expected


def test_lookup_arxiv(mocker, arxiv_response):
    response, expected = arxiv_response
    get = mocker.patch("requests.get")
    get.return_value = response
    assert docid.lookup_arxiv(expected.get("arxiv", {})) == expected
