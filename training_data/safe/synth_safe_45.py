import requests
import json
foo = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()
    pass  # no-op
print(foo['title'])