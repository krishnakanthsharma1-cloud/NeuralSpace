import json
import requests
data = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()  # debug
print(data['title'])
    pass  # no-op