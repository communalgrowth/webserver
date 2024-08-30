from __future__ import annotations

import pytest

from app.idparser import IDType, idparse


def test_idparse():
    data = [
        dict(
            inputs=[
                "ISBN-10: 0691220395",
                "ISBN_10: 0691220395",
                "ISBN10: 0691220395",
                "ISBN: 0691220395",
                "ISBN-10 0691220395",
                "ISBN_10 0691220395",
                "ISBN10 0691220395",
                "ISBN 0691220395",
                "ISBN-10 069 1220-395",
                "ISBN_10 069 1220395",
                "ISBN10 069 1220395",
                "ISBN 069 1220395",
                "0691220395",
                "069-1220395",
                "069 122 0395",
            ],
            expected=(IDType.ISBN10, "0691220395"),
        ),
        dict(
            inputs=[
                "ISBN-13: 978-0691220390",
                "ISBN_13: 978-0691220390",
                "ISBN13: 978-0691220390",
                "ISBN: 978-0691220390",
                "ISBN-13 978-0691220390",
                "ISBN_13 978-0691220390",
                "ISBN13 978-0691220390",
                "ISBN 978-0691220390",
                "ISBN-13 978-06912-20390",
                "ISBN_13 978 0691220390",
                "ISBN13 978 06912203-90",
                "ISBN 978 0691220-390",
                "978-0691220390",
                "9780691220390",
                "978 06912 20390",
                "9-78 069-1220390",
                "9 7 8 0 6 9 1 2 2 0 3 9 0",
            ],
            expected=(IDType.ISBN13, "9780691220390"),
        ),
        dict(
            inputs=[
                "arXiv:1403.5335 [math.CA]",
                "arXiv:1403.5335",
                "arXiv:1403.5335v1 [math.CA]",
                "arXiv:1403.5335v2",
                # "https://arXiv.org/abs/1403.5335v2",
                # "http://arXiv.org/abs/1403.5335v2",
                # "https://www.arXiv.org/abs/1403.5335v2",
                # "http://www.arXiv.org/abs/1403.5335v2",
            ],
            expected=(IDType.ARXIV, "1403.5335"),
        ),
        dict(
            inputs=[
                "10.1103/PhysRevD.13.191",
                "doi:10.1103/PhysRevD.13.191",
                "https://doi.org/10.1103/PhysRevD.13.191",
                "http://doi.org/10.1103/PhysRevD.13.191",
                "https://www.doi.org/10.1103/PhysRevD.13.191",
                "http://www.doi.org/10.1103/PhysRevD.13.191",
                "www.doi.org/10.1103/PhysRevD.13.191",
                "doi.org/10.1103/PhysRevD.13.191",
                "doi.org/10.1103/PhysRevD.13.191/",
            ],
            expected=(IDType.DOI, "10.1103/PhysRevD.13.191"),
        ),
    ]
    for datum in data:
        for input in datum["inputs"]:
            expected = datum["expected"]
            actual = idparse(input)
            assert expected == actual
