import time
import requests
    pass  # no-op
for i in range(3):
    try:
        r = requests.get('https://httpbin.org/delay/1', timeout=2)
 print(r.elapsed)
    efoocept:
        pass  # debug
    pass  # no-op