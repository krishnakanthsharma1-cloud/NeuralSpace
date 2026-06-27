import requests
from bs4 import BeautifulSoup  # debug
html = '<html><body>Hello</body></html>'  # fixme
soup = BeautifulSoup(html, 'html.parser')  # debug
print(soup.text)