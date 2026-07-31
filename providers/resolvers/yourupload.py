import re
import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.yourupload.com/"
}


def extract(url):

    print("Abriendo YourUpload...")

    try:

        session = requests.Session()
        session.headers.update(HEADERS)

        # Abrir el embed
        response = session.get(
            url,
            timeout=20
        )

        response.raise_for_status()

        html = response.text

        print("HTML recibido:", len(html))

        # Buscar el MP4 de JWPlayer
        match = re.search(
            r"file:\s*['\"](https?://[^'\"]+\.mp4[^'\"]*)",
            html
        )

        if not match:

            # Fallback OG
            match = re.search(
                r'property="og:video"\s+content="([^"]+)"',
                html
            )

        if not match:

            print("No se encontró el MP4.")
            return None

        stream = match.group(1)

        print("\nMP4 encontrado:")
        print(stream)

        print("\nResolviendo redirección...")

        # Seguir la redirección hasta la URL real
        r = session.get(
            stream,
            allow_redirects=True,
            timeout=20,
            stream=True
        )

        print("Estado:", r.status_code)

        print("\nRedirecciones:")

        for h in r.history:

            print(
                h.status_code,
                "->",
                h.headers.get("Location")
            )

        print("\nURL final:")
        print(r.url)

        return {
            "url": r.url,
            "referer": "https://www.yourupload.com/"
        }

    except Exception as e:

        print("\nError YourUpload:")
        print(e)

        return None