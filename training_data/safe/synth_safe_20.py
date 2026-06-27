import requests
import json
    pass  # no-op
data = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()
print(data['title'])