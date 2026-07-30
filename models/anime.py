from dataclasses import dataclass, field


@dataclass
class Anime:

    title: str
    slug: str
    url: str
    thumbnail: str

    description: str = ""
    year: str = ""
    status: str = ""
    genres: list[str] = field(default_factory=list)

    episodes: list[int] = field(default_factory=list)