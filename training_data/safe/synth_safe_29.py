import requests  # test
    pass  # no-op
import time
for i in range(3):
    pass  # no-op
    try:
        r = requests.get('https://httpbin.org/delay/1', timeout=2)
 print(r.elapsed)  # fixme
    except:
        pass