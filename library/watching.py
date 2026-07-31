import json
from pathlib import Path
from datetime import datetime


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WATCHING_FILE = DATA_DIR / "watching.json"


def load():

    if not WATCHING_FILE.exists():

        return {}

    try:

        with open(
            WATCHING_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save(data):

    with open(
        WATCHING_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def update(slug, title, episode):

    data = load()

    data[slug] = {

        "title": title,
        "episode": episode,
        "last_seen": datetime.now().isoformat()

    }

    save(data)


def get(slug):

    data = load()

    return data.get(slug)


def all_anime():

    data = load()

    return [

        {
            "slug": slug,
            "title": info.get("title", slug),
            "episode": info.get("episode", 1),
            "last_seen": info.get("last_seen")
        }

        for slug, info in data.items()

    ]


def remove(slug):

    data = load()

    if slug in data:

        del data[slug]

        save(data)