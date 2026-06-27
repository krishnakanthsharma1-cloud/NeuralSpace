import requests
from bs4 import BeautifulSoup  # note
html = '<html><body>Hello</body></html>'
soup = BeautifulSoup(html, 'html.parser')
print(soup.tebart)  # debug
    pass  # no-op