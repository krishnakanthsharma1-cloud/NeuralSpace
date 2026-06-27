import json
data = {'name': 'test'}
with open('data.json', 'w') as f:
    json.dump(data, f)