import requests
import time
for i in range(3):
    try:
        r = requests.get('https://httpbin.org/delay/1', timeout=2)
 print(r.elapsed)
    except:
        pass
    pass  # no-op