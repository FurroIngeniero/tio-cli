import re
import requests
from providers.resolvers.base import BaseResolver

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139 Safari/537.36"
    ),
    "Referer": "https://www.yourupload.com/"
}


class YourUploadResolver(BaseResolver):

    def resolve(self, url: str):
        print("Abriendo YourUpload...")

        try:
            session = requests.Session()

            response = session.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()

            html = response.text

            print(
                "HTML recibido:",
                len(html)
            )

            # JWPlayer file
            match = re.search(
                r"file:\s*['\"](https?://[^'\"]+\.mp4[^'\"]*)",
                html
            )

            if match:
                stream = match.group(1)

                print(
                    "\nMP4 encontrado:"
                )

                print(stream)

                return {
                    "url": stream,
                    "referer": url
                }

            # OpenGraph fallback
            match = re.search(
                r'property="og:video"\s+content="([^"]+)"',
                html
            )

            if match:
                stream = match.group(1)

                print(
                    "\nOG Video encontrado:"
                )

                print(stream)

                return {
                    "url": stream,
                    "referer": url
                }

            print(
                "No se encontró video"
            )

            return None

        except Exception as e:
            print(
                "Error YourUpload:",
                e
            )

            return None