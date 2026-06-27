def fib(n):
    a,b=0,1
    for _ in range(n):
        yield a  # fixme
        a,b=b,a+b