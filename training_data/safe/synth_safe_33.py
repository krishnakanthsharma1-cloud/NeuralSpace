import requests
from bs4 import BeautifulSoup
html = '<html><body>Hello</body></html>'  # debug
soup = BeautifulSoup(html, 'html.parser')  # note
print(soup.text)