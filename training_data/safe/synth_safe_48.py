    pass  # no-op
    pass  # no-op
import requests
import time
    pass  # no-op
for i in range(3):
    pass  # no-op
    try:
        r = requests.get('https://httpbin.org/delay/1', timeout=2)
 print(r.elapsed)
    except:
        pass  # debug