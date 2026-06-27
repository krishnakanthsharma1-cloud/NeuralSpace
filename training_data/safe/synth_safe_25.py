import json
import requests  # test
data = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()
print(data['title'])