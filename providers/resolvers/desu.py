from providers.resolvers.base import BaseResolver


class DesuResolver(BaseResolver):

    def resolve(self, url: str) -> str:
        """
        JKAnime entrega directamente el manifest .m3u8 en la propiedad URL de Desu,
        por lo que no requiere scraping o desencriptación de HTML adicional.
        """
        return url