from providers.resolvers.desu import DesuResolver
from providers.resolvers.voe import VoeResolver
from providers.resolvers.yourupload import YourUploadResolver

voe_resolver = VoeResolver()
yourupload_resolver = YourUploadResolver()
desu_resolver = DesuResolver()


def is_supported(server) -> bool:
    """Devuelve True solo si el servidor tiene un extractor soportado."""
    nombre = server.name.lower()
    servidores_soportados = ["voe", "yourupload", "desu", "magi"]
    return any(s in nombre for s in servidores_soportados)


def resolve(server):
    nombre = server.name.lower()
    url = server.url

    if "voe" in nombre:
        return voe_resolver.resolve(url)

    elif "yourupload" in nombre:
        return yourupload_resolver.resolve(url)

    elif "desu" in nombre or "magi" in nombre:
        return desu_resolver.resolve(url)

    return None