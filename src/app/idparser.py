import re


def strip_isbn(s: str):
    """Strips the ISBN part of an ISBN id"""
    if not hasattr(strip_isbn, "r"):
        setattr(strip_isbn, "r", re.compile("isbn", re.I))
    if strip_isbn.r.match(s):
        s = s[4:].lstrip()
        if (
            s.startswith("-10")
            or s.startswith("-13")
            or s.startswith("_10")
            or s.startswith("_13")
        ):
            s = s[3:].lstrip()
        if s.startswith(":"):
            s = s[1:].lstrip()
    return s


def match_isbn10(s: str):
    s = strip_isbn(s)
    s = re.sub("[-_]", "", s)
    return len(s) == 10 and s.isdigit()


def match_isbn13(s: str):
    s = strip_isbn(s)
    s = re.sub("[-_]", "", s)
    return len(s) == 13 and s.isdigit()


def idparse(s: str):
    """Identify the type of format followed by s

    Can be one of:
    1. ISBN-10
    2. ISBN-13
    3. DOI
    4. arXiv
    5. Generic string
    """
    return s
