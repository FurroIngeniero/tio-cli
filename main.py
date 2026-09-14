import providers.jkanime as jkanime
import providers.tioanime as tioanime
from library import all_anime, get, update
from player import play
from providers.resolvers import resolve


def elegir(maximo, mensaje, minimo=1):
    """
    Permite elegir una opción numérica. Soporta mínimo 0 para permitir opciones de 'Volver'.
    """
    while True:
        opcion = input(mensaje)
        if not opcion.isdigit():
            print("Ingresa un número válido.")
            continue

        opcion = int(opcion)
        if minimo <= opcion <= maximo:
            return opcion

        print("Opción inválida.")


def reproducir(servidores):
    print("\n========== SERVIDORES ==========\n")

    SERVIDORES_SOPORTADOS = ["voe", "yourupload", "desu", "magi"]

    # 1. Filtrar servidores soportados y deduplicar por URL
    servidores_filtrados = []
    urls_vistas = set()

    for servidor in servidores:
        nombre = servidor.name.lower()
        if any(p in nombre for p in SERVIDORES_SOPORTADOS):
            if servidor.url not in urls_vistas:
                urls_vistas.add(servidor.url)
                servidores_filtrados.append(servidor)

    # 2. Si no hay servidores soportados válidos
    if not servidores_filtrados:
        print("No hay servidores soportados disponibles para este episodio.\n")
        return False

    # 3. Mostrar lista limpia con opción de regresar
    for i, servidor in enumerate(servidores_filtrados, start=1):
        print(f"{i}. 🟢 {servidor.name}")
    print("0. ↩️  Volver al menú de opciones")

    print()

    # 4. Selección del usuario
    opcion = elegir(len(servidores_filtrados), "Servidor: ", minimo=0)
    
    if opcion == 0:
        return False

    servidor = servidores_filtrados[opcion - 1]

    print("\n========== SERVIDOR ==========\n")
    print(servidor.name)
    print(servidor.url)

    print(f"\nExtrayendo {servidor.name}...")
    stream = resolve(servidor)

    if not stream:
        print("\nNo se pudo extraer el stream.")
        return False

    print("\n========== STREAM ==========\n")

    if isinstance(stream, dict):
        print(stream["url"])
        play(stream["url"], stream.get("referer"))
    else:
        print(stream)
        play(stream)
        
    return True


def obtener_servidores_unificados(slug_tio: str, anime_title: str, episodio: int):
    """
    Obtiene servidores primarios (TioAnime) y secundarios (JKAnime para Desu/Magi).
    Incluye fallback de búsqueda si el nombre difiere.
    """
    servidores_raw = tioanime.get_servers(slug_tio, episodio) or []

    # Intento 1: Buscar en JKAnime por el título exacto
    resultados_jk = jkanime.search(anime_title)

    # Intento 2: Buscar por el slug formateado (si el título falla)
    if not resultados_jk:
        query_fallback = slug_tio.replace("-", " ")
        resultados_jk = jkanime.search(query_fallback)

    # Extracción de servidor Desu / Magi
    if resultados_jk:
        try:
            servidores_jk = jkanime.get_servers(resultados_jk[0].slug, episodio)
            if servidores_jk:
                servidores_raw.extend(servidores_jk)
        except Exception as e:
            print(f"[Warning JKAnime]: No se pudieron obtener servidores secundarios ({e})")

    return servidores_raw

def buscar_anime():
    query = input("\nBuscar anime (o presiona Enter para cancelar): ").strip()
    if not query:
        return

    resultados = tioanime.search(query)

    if not resultados:
        print("No se encontraron resultados.")
        return

    print("\n========== RESULTADOS ==========\n")
    for i, anime in enumerate(resultados, start=1):
        print(f"{i}. {anime.title}")
    print("0. ↩️  Volver al menú principal")

    print()
    opcion_anime = elegir(len(resultados), "Anime: ", minimo=0)
    if opcion_anime == 0:
        return

    anime_ref = resultados[opcion_anime - 1]
    anime = tioanime.get_anime(anime_ref.slug)

    progreso = get(anime.slug)
    episodios = sorted(anime.episodes)

    if progreso:
        print("\n========== PROGRESO ==========\n")
        print(f"Último capítulo visto: {progreso['episode']}\n")
        print("1. Continuar")
        print("2. Elegir capítulo")
        print("0. Volver atrás")

        opcion = elegir(2, "Opción: ", minimo=0)
        if opcion == 0:
            return
        episodio = progreso["episode"] if opcion == 1 else None
    else:
        episodio = None

    while True:
        if episodio is None:
            print("\n========== CAPÍTULOS ==========\n")
            for i, ep in enumerate(episodios, start=1):
                print(f"{i}. Episodio {ep}")
            print("0. ↩️  Volver atrás")

            print()
            indice = elegir(len(episodios), "Capítulo: ", minimo=0)
            if indice == 0:
                return
            episodio = episodios[indice - 1]

        print(f"\nReproduciendo episodio {episodio}")
        update(anime.slug, anime.title, episodio)

        servidores = obtener_servidores_unificados(anime.slug, anime.title, episodio)

        if not servidores:
            print("No hay servidores disponibles.")
            episodio = None
            continue

        reproducir(servidores)

        while True:
            print("\n========== OPCIONES ==========\n")
            print("1. Siguiente capítulo")
            print("2. Capítulo anterior")
            print("3. Elegir capítulo")
            print("4. Repetir capítulo")
            print("5. Cambiar servidor")
            print("0. ↩️  Volver al menú principal")

            opcion = elegir(5, "Opción: ", minimo=0)

            if opcion == 1:
                pos = episodios.index(episodio)
                if pos < len(episodios) - 1:
                    episodio = episodios[pos + 1]
                else:
                    print("Ya estás en el último capítulo.")
                break

            elif opcion == 2:
                pos = episodios.index(episodio)
                if pos > 0:
                    episodio = episodios[pos - 1]
                else:
                    print("Ya estás en el primer capítulo.")
                break

            elif opcion == 3:
                episodio = None
                break

            elif opcion == 4:
                # Repetir el episodio actual
                break

            elif opcion == 5:
                # Volver a intentar reproducir/cambiar servidor
                break

            elif opcion == 0:
                return


def continuar():
    while True:
        viendo = all_anime()

        if not viendo:
            print("\nNo tienes animes en seguimiento.\n")
            return

        print("\n========== CONTINUAR VIENDO ==========\n")
        for i, anime in enumerate(viendo, start=1):
            titulo = anime["title"] or anime["slug"]
            print(f"{i}. {titulo} (Cap. {anime['episode']})")
        print("0. ↩️  Volver al menú principal")

        print()
        opcion_anime = elegir(len(viendo), "Anime: ", minimo=0)
        
        if opcion_anime == 0:
            return

        anime_select = viendo[opcion_anime - 1]
        anime_real = tioanime.get_anime(anime_select["slug"])

        episodios = sorted(anime_real.episodes)
        episodio = anime_select["episode"]

        while True:
            if episodio is None:
                print("\n========== CAPÍTULOS ==========\n")
                for i, ep in enumerate(episodios, start=1):
                    print(f"{i}. Episodio {ep}")
                print("0. ↩️  Volver a la lista de animes")

                print()
                indice = elegir(len(episodios), "Capítulo: ", minimo=0)
                if indice == 0:
                    break
                episodio = episodios[indice - 1]

            print(f"\nReproduciendo episodio {episodio}")
            update(anime_real.slug, anime_real.title, episodio)

            servidores = obtener_servidores_unificados(anime_real.slug, anime_real.title, episodio)

            if not servidores:
                print("No hay servidores disponibles.")
                episodio = None
                continue

            reproducir(servidores)

            while True:
                print("\n========== OPCIONES ==========\n")
                print("1. Siguiente capítulo")
                print("2. Capítulo anterior")
                print("3. Elegir capítulo")
                print("4. Repetir capítulo")
                print("5. Cambiar servidor")
                print("6. ↩️  Volver a la lista de animes")
                print("0. 🏠 Volver al menú principal")

                opcion = elegir(6, "Opción: ", minimo=0)

                if opcion == 1:
                    pos = episodios.index(episodio)
                    if pos < len(episodios) - 1:
                        episodio = episodios[pos + 1]
                    else:
                        print("Ya estás en el último capítulo.")
                    break

                elif opcion == 2:
                    pos = episodios.index(episodio)
                    if pos > 0:
                        episodio = episodios[pos - 1]
                    else:
                        print("Ya estás en el primer capítulo.")
                    break

                elif opcion == 3:
                    episodio = None
                    break

                elif opcion == 4:
                    # Repetir el mismo episodio
                    break

                elif opcion == 5:
                    # Permite elegir otro servidor del mismo capitulo
                    break

                elif opcion == 6:
                    # Rompe el bucle del episodio activo para volver a la lista de seguimiento
                    break

                elif opcion == 0:
                    return

            if opcion in (6, 0):
                break


def main():
    while True:
        print("\n========== TIO-CLI ==========\n")
        print("1. Continuar viendo")
        print("2. Buscar anime")
        print("0. Salir")

        opcion = elegir(2, "Opción: ", minimo=0)

        if opcion == 1:
            continuar()
        elif opcion == 2:
            buscar_anime()
        elif opcion == 0:
            print("¡Hasta luego!")
            break


if __name__ == "__main__":
    main()