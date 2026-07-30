from providers.resolvers.base import BaseResolver


class MegaResolver(BaseResolver):

    def resolve(self, url: str) -> str:
        raise NotImplementedError("Mega aún no implementado")