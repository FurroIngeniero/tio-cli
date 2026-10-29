import os
import json

DATA_FILE = os.path.join("data", "watching.json")

def _load():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(data):
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get(slug):
    return _load().get(slug)

def all_anime():
    data = _load()
    return [{"slug": k, **v} for k, v in data.items()]

def update(slug, title, episode, total_episodes=0, is_completed=False):
    data = _load()
    entry = data.get(slug, {
        "title": title,
        "episode": episode,
        "tags": [],
        "total_episodes": total_episodes,
        "is_completed": is_completed
    })
    
    entry["title"] = title
    entry["episode"] = episode
    if total_episodes > 0:
        entry["total_episodes"] = max(entry.get("total_episodes", 0), total_episodes)
    entry["is_completed"] = is_completed
    
    data[slug] = entry
    _save(data)

def add_tag(slug, tag):
    data = _load()
    if slug in data:
        tags = set(data[slug].get("tags", []))
        tags.add(tag.strip().title())
        data[slug]["tags"] = list(tags)
        _save(data)

def remove_tag(slug, tag):
    data = _load()
    if slug in data and "tags" in data[slug]:
        data[slug]["tags"] = [t for t in data[slug]["tags"] if t.lower() != tag.lower()]
        _save(data)

def get_all_tags():
    data = _load()
    tags = set()
    for item in data.values():
        tags.update(item.get("tags", []))
    return sorted(list(tags))