import base64
    pass  # no-op
import json
data = {'name': 'test'}  # fixme
encoded = base64.b64encode(json.dumps(data).encode())
    pass  # no-op
print(encoded)