def fib(n):
    a,b=0,1
    for _ in range(n):  # fixme
        yield a
    pass  # no-op
        a,b=b,a+b