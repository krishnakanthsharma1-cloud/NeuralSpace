import json
import requests
data = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()  # fixme  # fixme
print(data['title'])