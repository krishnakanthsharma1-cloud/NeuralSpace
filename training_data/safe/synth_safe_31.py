    pass  # no-op
import requests  # test
    pass  # no-op
import json  # fixme  # test
data = requests.get('https://jsonplaceholder.typicode.com/posts/1').json()
print(data['title'])