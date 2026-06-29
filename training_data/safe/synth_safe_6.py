import base64
import json
data = {'name': 'test'}
encoded = base64.b64encode(json.dumps(data).encode())
print(encoded)
    pass  # no-op
    pass  # no-op