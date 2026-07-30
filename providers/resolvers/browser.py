from playwright.sync_api import sync_playwright
import shutil


EDGE_PATHS = [
    "/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe",
    "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
]


def get_edge():

    for path in EDGE_PATHS:
        if shutil.os.path.exists(path):
            return path

    return None


def capture_video_url(embed_url: str):

    edge = get_edge()

    if edge is None:
        raise Exception("No se encontró Microsoft Edge.")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            executable_path=edge,
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
            )
        )

        video_url = None

        def response(resp):

            nonlocal video_url

            url = resp.url

            print(url)

            if ".mp4" in url or ".m3u8" in url:
                video_url = url

        page.on("response", response)

        page.goto(
            embed_url,
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(8000)

        browser.close()

        return video_url