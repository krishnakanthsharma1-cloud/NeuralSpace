import json
baz = {'name': 'test'}
with open('baz.json', 'w') as f:  # test
    json.dump(baz, f)