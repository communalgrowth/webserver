from __future__ import annotations

import pytest

from app import docid


class MockResponse:
    """A mock requests response"""

    def __init__(self, code, data={}, text=""):
        self.status_code = code
        self.data = data
        self.text = text

    def json(self):
        return self.data


@pytest.fixture(
    params=[
        (MockResponse(200), MockResponse(200), {}),
        (MockResponse(100), MockResponse(200), {}),
        (MockResponse(200), MockResponse(100), {}),
        (MockResponse(100), MockResponse(100), {}),
        (
            MockResponse(
                200,
                dict(
                    title="Fantastic Mr. Fox",
                    subtitle="",
                    publish_date="October 1, 1988",
                    isbn_10=["0140328726"],
                    isbn_13=["9780140328721"],
                ),
            ),
            MockResponse(200, dict(docs=[dict(author_name=["Roald Dahl"])])),
            dict(
                title="Fantastic Mr. Fox",
                subtitle="",
                published="1988-10-01T00:00:00Z",
                authors=["R. Dahl"],
                isbn10="0140328726",
                isbn13="9780140328721",
            ),
        ),
    ]
)
def isbn_and_author_response(request):
    return request.param


@pytest.fixture(
    params=[
        (MockResponse(200), {}),
        (MockResponse(100), {}),
        (MockResponse(200), {}),
        (MockResponse(100), {}),
        (
            MockResponse(
                200,
                dict(
                    message=dict(
                        title=["Black hole explosions?"],
                        author=[dict(given="S. W.", family="HAWKING")],
                        published={"date-parts": [[1974, 3, 1]]},
                    )
                ),
            ),
            dict(
                title="Black hole explosions?",
                published="1974-03-01T00:00:00Z",
                authors=["S. W. Hawking"],
                doi="10.1038/248030a0",
            ),
        ),
    ],
)
def doi_response(request):
    return request.param


@pytest.fixture(
    params=[
        (MockResponse(200), {}),
        (MockResponse(100), {}),
        (MockResponse(200), {}),
        (MockResponse(100), {}),
        (
            MockResponse(
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
            dict(
                title="Rigidity, graphs and Hausdorff dimension",
                published="2017-08-20T01:41:17Z",
                authors=[
                    "N. Chatzikonstantinou",
                    "A. Iosevich",
                    "S. Mkrtchyan",
                    "J. Pakianathan",
                ],
                arxiv="1708.05919",
            ),
        ),
    ]
)
def arxiv_response(request):
    return request.param
