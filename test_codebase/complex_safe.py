# complex_safe.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)

def fetch_prices(url):
    response = requests.get(url, timeout=5)
    soup = BeautifulSoup(response.text, 'html.parser')
    prices = [float(item.text.strip('$')) for item in soup.select('.price')]
    return pd.Series(prices)

if __name__ == "__main__":
    data = fetch_prices("https://example.com/prices")
    print(data.describe())
    time.sleep(0.5)