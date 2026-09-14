import json
import re
from bs4 import BeautifulSoup

from models.anime import Anime
from models.server import Server
from utils.request import get

BASE_URL = "https://jkanime.net"


def search(query: str):
    response = get(f"{BASE_URL}/buscar/", params={"q": query})
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for item in soup.select(".anime__item, .bloque, .portada-box, div.col-lg-3, div.col-6"):
        a = item.select_one("a[href*='jkanime.net']") or item.select_one("a")
        if not a or not a.get("href"):
            continue

        href = a["href"]
        if href.startswith("javascript") or "/buscar" in href:
            continue

        slug = href.strip("/").split("/")[-1]
        title_el = item.select_one("h5, h3, .title, h2, div.title-anime")
        title = title_el.get_text(strip=True) if title_el else slug.replace("-", " ").title()

        img_el = item.select_one("img")
        thumbnail = ""
        if img_el:
            thumbnail = img_el.get("src") or img_el.get("data-src", "")
            if thumbnail.startswith("/"):
                thumbnail = BASE_URL + thumbnail

        results.append(
            Anime(title=title, slug=slug, url=f"{BASE_URL}/{slug}/", thumbnail=thumbnail)
        )

    return results


def get_anime(slug: str):
    response = get(f"{BASE_URL}/{slug}/")
    soup = BeautifulSoup(response.text, "html.parser")

    title_el = soup.select_one(".sinopsis h2, .anime__details__title h3, div.titulos h1")
    title = title_el.get_text(strip=True) if title_el else slug.replace("-", " ").title()

    thumbnail = ""
    img_el = soup.select_one(".anime__details__pic, .portada img, .sinopsis img")
    if img_el:
        thumbnail = img_el.get("src") or img_el.get("data-src", "")
        if thumbnail.startswith("/"):
            thumbnail = BASE_URL + thumbnail

    return Anime(
        title=title, slug=slug, url=f"{BASE_URL}/{slug}/", thumbnail=thumbnail, episodes=[]
    )


def get_servers(slug: str, episode: int):
    """
    Extrae ÚNICAMENTE Desu y Magi filtrando reproducciones duplicadas.
    """
    url = f"{BASE_URL}/{slug}/{episode}/"
    response = get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    servers = []
    found_urls = set()
    raw_sources = []

    for iframe in soup.select("iframe.player_conte, iframe[src*='jkplayer'], iframe[src*='/c1.php'], iframe[src*='/c2.php']"):
        src = iframe.get("src") or iframe.get("data-src", "")
        if src:
            raw_sources.append(src)

    if not raw_sources:
        matches = re.findall(r'src=["\']([^"\']*(?:jkplayer|c1\.php|c2\.php|um)[^"\']*)["\']', html, re.I)
        raw_sources.extend(matches)

    for src in raw_sources:
        if not src or src.startswith("#"):
            continue

        src = _normalize_url(src)
        name = _check_server_name(src)

        if name:
            final_stream_url = _extract_m3u8(src)
            # Filtro de unicidad
            if final_stream_url not in found_urls:
                found_urls.add(final_stream_url)
                servers.append(Server(name=name, url=final_stream_url, premium=False))

    return servers


def _check_server_name(url: str):
    val = url.lower()
    if "desu" in val or "c1.php" in val or "um" in val or "jkplayer/um" in val:
        return "Desu"
    elif "magi" in val or "c2.php" in val or "jkmagi" in val:
        return "Magi"
    return None


def _normalize_url(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    elif url.startswith("/"):
        return BASE_URL + url
    return url


def _extract_m3u8(embed_url: str) -> str:
    try:
        res = get(embed_url, headers={"Referer": f"{BASE_URL}/"})
        match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', res.text)
        if match:
            return match.group(1)
    except Exception:
        pass
    return embed_url