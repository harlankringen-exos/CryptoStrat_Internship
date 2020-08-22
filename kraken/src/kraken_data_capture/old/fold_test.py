import sys
import functools
import itertools

foldl = lambda func, acc, xs: functools.reduce(func, xs, acc)
 
def prepend(value, iterator):
    "Prepend a single value in front of an iterator"
    # prepend(1, [2, 3, 4]) -> 1 2 3 4
    return chain([value], iterator)
 
def read_par(fobj):
    for line in fobj.readlines():
        yield line

def alpha(acc,x):
    x = list(x)
    x.sort()
    acc.append(x[0])
    return acc

connector_files = sys.argv[1:]
connectors = list(map(open, connector_files))    

m = list(map(read_par, connectors))
res = foldl(alpha, [], zip(*map(open,connector_files)))

"""while True:
    lines = list(map(next, m))
    if not lines:
        break
    else:
        res = foldl(alpha, [], lines)
        print(res)
"""
