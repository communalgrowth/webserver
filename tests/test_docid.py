from __future__ import annotations

import pytest

from app import docid


class MyResponse:
    def __init__(self, code, data={}, text=""):
        self.status_code = code
        self.data = data
        self.text = text

    def json(self):
        return self.data


@pytest.mark.parametrize(
    "response, expected",
    [
        (MyResponse(200), True),
        (MyResponse(300), False),
        (MyResponse(101), False),
    ],
)
def test_ok_response(response, expected):
    assert docid.ok_response(response) == expected


@pytest.mark.parametrize(
    "isbn_response, author_response, expected",
    [
        (MyResponse(200), MyResponse(200), None),
        (MyResponse(100), MyResponse(200), None),
        (MyResponse(200), MyResponse(100), None),
        (MyResponse(100), MyResponse(100), None),
        (
            MyResponse(
                200,
                dict(
                    title="Fantastic Mr. Fox",
                    subtitle="",
                    publish_date="October 1, 1988",
                    isbn_10=["0140328726"],
                    isbn_13=["9780140328721"],
                ),
            ),
            MyResponse(200, dict(docs=[dict(author_name=["Roald Dahl"])])),
            (
                "Fantastic Mr. Fox",
                "",
                "1988-10-01T00:00:00Z",
                ["R. Dahl"],
                "0140328726",
                "9780140328721",
            ),
        ),
    ],
)
def test_resolve_isbn(mocker, isbn_response, author_response, expected):
    get = mocker.patch("requests.get")
    get.side_effect = [isbn_response, author_response]
    assert docid.resolve_isbn("0140328726") == expected


@pytest.mark.parametrize(
    "doi_response, expected",
    [
        (MyResponse(200), None),
        (MyResponse(100), None),
        (MyResponse(200), None),
        (MyResponse(100), None),
        (
            MyResponse(
                200,
                dict(
                    message=dict(
                        title=["Black hole explosions?"],
                        author=[dict(given="S. W.", family="HAWKING")],
                        published={"date-parts": [[1974, 3, 1]]},
                    )
                ),
            ),
            (
                "Black hole explosions?",
                "1974-03-01T00:00:00Z",
                ["S. W. Hawking"],
                "10.1038/248030a0",
            ),
        ),
    ],
)
def test_resolve_doi(mocker, doi_response, expected):
    get = mocker.patch("requests.get")
    get.side_effect = [doi_response]
    assert docid.resolve_doi("10.1038/248030a0") == expected


@pytest.mark.parametrize(
    "arxiv_response, expected",
    [
        (MyResponse(200), None),
        (MyResponse(100), None),
        (MyResponse(200), None),
        (MyResponse(100), None),
        (
            MyResponse(
                200,
                text="""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
      <published>2017-08-20T01:41:17Z</published>
      <title>Rigidity, graphs and Hausdorff dimension</title>
      <author>
        <name>N. Chatzikonstantinou</name>
      </author>
      <author>
        <name>A. Iosevich</name>
      </author>
      <author>
        <name>S. Mkrtchyan</name>
      </author>
      <author>
        <name>J. Pakianathan</name>
      </author>
  </entry>
</feed>
""",
            ),
            (
                "Rigidity, graphs and Hausdorff dimension",
                "2017-08-20T01:41:17Z",
                [
                    "N. Chatzikonstantinou",
                    "A. Iosevich",
                    "S. Mkrtchyan",
                    "J. Pakianathan",
                ],
                "1708.05919",
            ),
        ),
    ],
)
def test_resolve_arxiv(mocker, arxiv_response, expected):
    get = mocker.patch("requests.get")
    get.side_effect = [arxiv_response]
    assert docid.resolve_arxiv("1708.05919") == expected
