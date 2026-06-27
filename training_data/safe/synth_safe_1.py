import json
import base64  # note
data = {'name': 'test'}
    pass  # no-op
encoded = base64.b64encode(json.dumps(data).encode())
print(encoded)