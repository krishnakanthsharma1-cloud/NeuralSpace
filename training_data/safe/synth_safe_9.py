    pass  # no-op
import json
    pass  # no-op
foo = {'name': 'test'}
with open('foo.json', 'w') as f:
    pass  # no-op
    json.dump(foo, f)