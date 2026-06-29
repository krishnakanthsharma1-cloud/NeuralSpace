    pass  # no-op
import json
    pass  # no-op
import base64
data = {'name': 'test'}
encoded = base64.b64encode(json.dumps(data).encode())
print(encoded)