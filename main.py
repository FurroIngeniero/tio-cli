from providers.tioanime import (
    search,
    get_anime,
    get_servers
)

from providers.resolvers.voe import extract as extract_voe
from providers.resolvers.yourupload import extract as extract_yourupload

from player import play

from library import (
    update,
    get,
    all_anime
)


def elegir(maximo, mensaje):

    while True:

        opcion = input(mensaje)

        if not opcion.isdigit():

            print("Ingresa un número.")
            continue

        opcion = int(opcion)

        if 1 <= opcion <= maximo:

            return opcion

        print("Opción inválida.")


def reproducir(servidores):

    servidor = servidores[
        elegir(
            len(servidores),
            "Servidor: "
        ) - 1
    ]

    print("\n========== SERVIDOR ==========\n")

    print(servidor.name)
    print(servidor.url)

    nombre = servidor.name.lower()

    stream = None

    if "voe" in nombre:

        print("\nExtrayendo Voe...")

        stream = extract_voe(
            servidor.url
        )

    elif "yourupload" in nombre:

        print("\nExtrayendo YourUpload...")

        stream = extract_yourupload(
            servidor.url
        )

    else:

        print("Servidor no soportado.")
        return

    if not stream:

        print("No se pudo extraer el stream.")
        return

    print("\n========== STREAM ==========\n")

    if isinstance(stream, dict):

        print(stream["url"])

        play(
            stream["url"],
            stream.get("referer")
        )

    else:

        print(stream)

        play(stream)


def buscar_anime():

    query = input(
        "Buscar anime: "
    ).strip()

    resultados = search(query)

    if not resultados:

        print("No se encontraron resultados.")
        return

    print()

    for i, anime in enumerate(
        resultados,
        start=1
    ):

        print(f"{i}. {anime.title}")

    anime = resultados[
        elegir(
            len(resultados),
            "Anime: "
        ) - 1
    ]

    anime = get_anime(
        anime.slug
    )

    progreso = get(
        anime.slug
    )

    episodios = sorted(
        anime.episodes
    )

    if progreso:

        print("\n========== PROGRESO ==========\n")

        print(
            f"Último capítulo visto: {progreso['episode']}"
        )

        print()

        print("1. Continuar")
        print("2. Elegir capítulo")

        opcion = elegir(
            2,
            "Opción: "
        )

        if opcion == 1:

            episodio = progreso["episode"]

        else:

            episodio = None

    else:

        episodio = None

    while True:

        if episodio is None:

            print(
                "\n========== CAPÍTULOS ==========\n"
            )

            for i, ep in enumerate(
                episodios,
                start=1
            ):

                print(
                    f"{i}. Episodio {ep}"
                )

            print()

            indice = elegir(
                len(episodios),
                "Capítulo: "
            )

            episodio = episodios[
                indice - 1
            ]

        print(
            f"\nReproduciendo episodio {episodio}"
        )

        print("Slug:", anime.slug)
        print("Título:", anime.title)

        update(
            anime.slug,
            anime.title,
            episodio
        )

        servidores = get_servers(
            anime.slug,
            episodio
        )

        if not servidores:

            print(
                "No hay servidores."
            )

            episodio = None
            continue

        reproducir(
            servidores
        )

        while True:

            print(
                "\n========== OPCIONES ==========\n"
            )

            print("1. Siguiente capítulo")
            print("2. Capítulo anterior")
            print("3. Elegir capítulo")
            print("4. Repetir capítulo")
            print("5. Volver al menú principal")
            print("6. Salir")

            opcion = elegir(
                6,
                "Opción: "
            )

            if opcion == 1:

                pos = episodios.index(
                    episodio
                )

                if pos < len(episodios) - 1:

                    episodio = episodios[
                        pos + 1
                    ]

                else:

                    print(
                        "Ya estás en el último capítulo."
                    )

                break

            elif opcion == 2:

                pos = episodios.index(
                    episodio
                )

                if pos > 0:

                    episodio = episodios[
                        pos - 1
                    ]

                else:

                    print(
                        "Ya estás en el primer capítulo."
                    )

                break

            elif opcion == 3:

                episodio = None
                break

            elif opcion == 4:

                pass

            elif opcion == 5:

                return

            else:

                print(
                    "Saliendo..."
                )

                raise SystemExit


def continuar():

    viendo = all_anime()

    if not viendo:

        print(
            "\nNo tienes animes en seguimiento.\n"
        )

        return

    print(
        "\n========== CONTINUAR VIENDO ==========\n"
    )

    for i, anime in enumerate(
        viendo,
        start=1
    ):

        print(
            f"{i}. {anime['title']} (Cap. {anime['episode']})"
        )

    print()

    anime = viendo[
        elegir(
            len(viendo),
            "Anime: "
        ) - 1
    ]

    anime_real = get_anime(
    anime["slug"]
    )

    episodios = sorted(
        anime_real.episodes
    )

    episodio = anime["episode"]

    while True:

        print(
            f"\nReproduciendo episodio {episodio}"
        )

        update(
            anime_real.slug,
            anime_real.title,
            episodio
        )

        servidores = get_servers(
        anime_real.slug,
        episodio
        )   

        if not servidores:

            print(
                "No hay servidores."
            )

            return

        reproducir(
            servidores
        )

        print()

        print("1. Siguiente capítulo")
        print("2. Salir")

        opcion = elegir(
            2,
            "Opción: "
        )

        if opcion == 1:

            pos = episodios.index(
                episodio
            )

            if pos < len(episodios) - 1:

                episodio = episodios[
                    pos + 1
                ]

            else:

                print(
                    "Último capítulo."
                )
                return

        else:

            return


def main():

    while True:

        print(
            "\n========== TIO-CLI ==========\n"
        )

        print("1. Continuar viendo")
        print("2. Buscar anime")
        print("3. Salir")

        opcion = elegir(
            3,
            "Opción: "
        )

        if opcion == 1:

            continuar()

        elif opcion == 2:

            buscar_anime()

        else:

            break


if __name__ == "__main__":

    main()