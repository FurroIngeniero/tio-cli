import requests

BASE_URL = "https://tioanime.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}


def get(path: str, **kwargs):
    """
    Realiza una petición GET a TioAnime.
    """

    url = BASE_URL + path

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15,
        **kwargs
    )

    response.raise_for_status()

    return response