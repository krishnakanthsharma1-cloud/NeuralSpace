import requests
import json
baz = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()
print(baz['title'])