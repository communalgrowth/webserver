def splitlines_clean(s):
    """Split lines, removing surrounding spaces, and empty or blank lines"""
    return [x.strip() for x in s.splitlines() if x and not x.isspace()]
