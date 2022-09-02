import requests
from bs4 import BeautifulSoup as bs


def fetch_youtube_views(url):
    content = requests.get(url)
    soup = bs(content.content, "html.parser")
    views = int(soup.select_one(
        'meta[itemprop="interactionCount"][content]')['content'])
    return views
