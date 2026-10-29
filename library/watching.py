import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WATCHING_FILE = DATA_DIR / "watching.json"
TAGS_FILE = DATA_DIR / "tags.json"


def load():
    if not WATCHING_FILE.exists():
        return {}
    try:
        with open(WATCHING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def remove(slug):
    data = load()
    if slug in data:
        del data[slug]
        save(data)
        
def save(data):
    with open(WATCHING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_global_tags():
    if not TAGS_FILE.exists():
        return []
    try:
        with open(TAGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_global_tags(tags_list):
    with open(TAGS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(set(tags_list))), f, indent=4, ensure_ascii=False)


def create_global_tag(tag):
    tag_clean = tag.strip().title()
    if not tag_clean:
        return
    tags = get_global_tags()
    if tag_clean not in tags:
        tags.append(tag_clean)
        save_global_tags(tags)


def delete_global_tag(tag):
    tags = get_global_tags()
    tags = [t for t in tags if t.lower() != tag.lower()]
    save_global_tags(tags)
    
    data = load()
    modified = False
    for item in data.values():
        if "tags" in item and tag.title() in item["tags"]:
            item["tags"] = [t for t in item["tags"] if t.lower() != tag.lower()]
            modified = True
    if modified:
        save(data)


def set_anime_tags(slug, tags_list):
    data = load()
    if slug not in data:
        data[slug] = {
            "title": slug.replace("-", " ").title(),
            "episode": 0,
            "last_seen": datetime.now().isoformat(),
            "tags": [],
            "total_episodes": 0,
            "is_completed": False
        }
        
    data[slug]["tags"] = sorted(list(set(tags_list)))
    save(data)


def update(slug, title, episode, total_episodes=0, is_completed=False):
    data = load()
    entry = data.get(slug, {})
    
    tags = set(entry.get("tags", []))
    prev_total = entry.get("total_episodes", 0)
    nuevo_total = max(prev_total, total_episodes)

    if is_completed and nuevo_total > 0 and episode >= nuevo_total:
        create_global_tag("Completado")
        tags.add("Completado")

    data[slug] = {
        "title": title,
        "episode": episode,
        "last_seen": datetime.now().isoformat(),
        "tags": sorted(list(tags)),
        "total_episodes": nuevo_total,
        "is_completed": is_completed
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
            "episode": info.get("episode", 0),
            "last_seen": info.get("last_seen"),
            "tags": info.get("tags", []),
            "total_episodes": info.get("total_episodes", 0),
            "is_completed": info.get("is_completed", False)
        }
        for slug, info in data.items()
    ]


def remove(slug):
    data = load()
    if slug in data:
        del data[slug]
        save(data)