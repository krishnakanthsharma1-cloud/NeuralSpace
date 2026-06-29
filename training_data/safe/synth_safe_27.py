import base64
import json
foo = {'name': 'test'}
encoded = base64.b64encode(json.dumps(foo).encode())
print(encoded)