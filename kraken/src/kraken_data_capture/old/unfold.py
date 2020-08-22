import itertools
import functools

def unfold(fun, fd):
     p = fun(fd)
     print("unfold sees:", p)
     if p[0] == []:
         return []
     else:
         return [p[0]] + (unfold(fun, p[1]))

def reader(fd):
    ln = fd.readline()
    print(ln)
    if  ln == '':
        return ([],fd)
    else:
        return (ln, fd)

fd = open('alpha1.txt', 'r')
print(unfold(reader, fd))
