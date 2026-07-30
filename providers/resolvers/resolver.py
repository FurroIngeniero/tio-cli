from providers.resolvers.yourupload import YourUploadResolver
from providers.resolvers.mega import MegaResolver
from providers.resolvers.okru import OkruResolver
from providers.resolvers.streamsb import StreamSBResolver
from providers.resolvers.filemoon import FileMoonResolver
from providers.resolvers.streamwish import StreamWishResolver


RESOLVERS = {
    "yourupload": YourUploadResolver(),
    "mega": MegaResolver(),
    "okru": OkruResolver(),
    "streamsb": StreamSBResolver(),
    "filemoon": FileMoonResolver(),
    "streamwish": StreamWishResolver(),
}


def resolve(server):
    key = server.name.lower().replace(" ", "")

    resolver = RESOLVERS.get(key)

    if resolver is None:
        raise Exception(f"No existe resolver para {server.name}")

    return resolver.resolve(server.url)