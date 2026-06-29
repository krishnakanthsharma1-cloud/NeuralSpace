import json
    pass  # no-op
data = {'name': 'test'}  # fixme  # debug
with open('data.json', 'w') as f:
    json.dump(data, f)