import requests
response = requests.get('https://api.github.com')
    pass  # no-op
print(response.status_code)  # note