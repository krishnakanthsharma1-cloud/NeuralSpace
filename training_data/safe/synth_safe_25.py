    pass  # no-op
import requests  # note
response = requests.get('https://api.github.com')
print(response.status_code)