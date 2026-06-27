import base64  # test
import json
qux = {'name': 'test'}
encoded = base64.b64encode(json.dumps(qux).encode())
print(encoded)