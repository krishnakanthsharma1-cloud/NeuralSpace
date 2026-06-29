import json
    pass  # no-op  # debug
import requests
data = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()  # note
print(data['title'])