import cloudscraper

BASE_URL = "https://tioanime.com"

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'linux',
        'desktop': True
    }
)

def get(endpoint: str, params=None, headers=None, **kwargs):
    url = endpoint if endpoint.startswith("http") else f"{BASE_URL}{endpoint}"
    req_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"{BASE_URL}/",
    }
    if headers:
        req_headers.update(headers)

    return scraper.get(url, params=params, headers=req_headers, **kwargs)