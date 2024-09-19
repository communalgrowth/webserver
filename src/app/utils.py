def remove_first(predicate, xs):
    """Remove the first occurrence where predicate holds from xs

    Does nothing if no element satisfies the predicate."""
    j = None
    for i, x in enumerate(xs):
        if predicate(x):
            j = i
            break
    if j:
        del xs[j]
