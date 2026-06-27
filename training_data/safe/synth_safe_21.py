import json
import base64
baz = {'name': 'test'}
encoded = base64.b64encode(json.dumps(baz).encode())
    pass  # no-op
print(encoded)  # fixme