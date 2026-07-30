import json
import re

from bs4 import BeautifulSoup

from models.anime import Anime
from models.server import Server
from utils.request import get, BASE_URL


def search(query: str):

    response = get(
        "/directorio",
        params={
            "q": query
        }
    )

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for article in soup.select("article.anime"):

        a = article.select_one("a")

        href = a["href"]

        slug = href.split("/")[-1]

        title = article.select_one("h3.title").get_text(strip=True)

        thumbnail = article.select_one("img")["src"]

        if thumbnail.startswith("/"):
            thumbnail = BASE_URL + thumbnail

        results.append(
            Anime(
                title=title,
                slug=slug,
                url=BASE_URL + href,
                thumbnail=thumbnail
            )
        )

    return results


def get_anime(slug: str):

    response = get(f"/anime/{slug}")

    html = response.text

    match = re.search(
        r'var episodes = \[(.*?)\];',
        html,
        re.DOTALL
    )

    episodes = []

    if match:

        episodes = [
            int(ep.strip())
            for ep in match.group(1).split(",")
            if ep.strip().isdigit()
        ]

    return Anime(
        title="",
        slug=slug,
        url=f"{BASE_URL}/anime/{slug}",
        thumbnail="",
        episodes=episodes
    )


def get_servers(slug: str, episode: int):

    response = get(f"/ver/{slug}-{episode}")

    html = response.text

    match = re.search(
        r'var videos = (\[.*?\]);',
        html,
        re.DOTALL
    )

    if not match:
        return []

    videos = match.group(1)

    videos = videos.replace("\\/", "/")

    data = json.loads(videos)

    servers = []

    for video in data:

        servers.append(
            Server(
                name=video[0],
                url=video[1],
                premium=bool(video[3])
            )
        )

    return servers