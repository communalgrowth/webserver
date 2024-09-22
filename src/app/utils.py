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
