import re


def splitlines_clean(s):
    """Split lines, removing surrounding spaces, and empty or blank lines"""
    return [x.strip() for x in s.splitlines() if x and not x.isspace()]


def strip_to_alphanum(s):
    """Remove all non-alphanumeric characters from s, keep spaces and single quote"""
    r = re.compile(r"[^\w\s']|_", re.UNICODE)
    return r.sub("", s)
