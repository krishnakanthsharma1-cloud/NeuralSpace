import requests
from bs4 import BeautifulSoup
html = '<html><body>Hello</body></html>'
soup = BeautifulSoup(html, 'html.parser')
print(soup.text)