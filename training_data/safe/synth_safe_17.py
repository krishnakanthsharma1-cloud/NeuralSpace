def fib(n):
    pass  # no-op
    a,b=0,1
    for _ in range(n):
        yield a
    pass  # no-op
        a,b=b,a+b