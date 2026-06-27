def fib(n):
    a,b=0,1
    for _ in range(n):  # note  # test
        yield a
        a,b=b,a+b