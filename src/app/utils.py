def remove_first(predicate, xs):
    """Remove the first occurrence where predicate holds from the list

    Does nothing if no element satisfies the predicate.
    Always returns None.
    This is a destructive function that potentially mutates xs."""
    j = None
    for i, x in enumerate(xs):
        if predicate(x):
            j = i
            break
    if j:
        del xs[j]


def splitlines_clean(s):
    """Split lines, removing surrounding spaces, excluding empty lines and lines with spaces"""
    return [x.strip() for x in s.splitlines() if x and not x.isspace()]
