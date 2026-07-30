import subprocess

from providers.tioanime import (
    search,
    get_anime,
    get_servers
)

from providers.resolvers.voe import extract as extract_voe
from providers.resolvers.yourupload import extract as extract_yourupload


VLC_PATH = "/mnt/c/Program Files/VideoLAN/VLC/vlc.exe"



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




def abrir_vlc(stream, referer=None):

    print("\nAbriendo VLC...")


    comando = [
        VLC_PATH,
        stream
    ]


    if referer:

        comando.extend(
            [
                f"--http-referrer={referer}",
                "--http-user-agent=Mozilla/5.0"
            ]
        )


    try:

        subprocess.run(
            comando
        )


        print(
            "\nVLC cerrado."
        )


    except Exception as e:

        print(
            "Error abriendo VLC:"
        )

        print(e)




def reproducir(servidores):


    servidor = servidores[
        elegir(
            len(servidores),
            "Servidor: "
        ) - 1
    ]


    print(
        "\n========== SERVIDOR ==========\n"
    )


    print(
        servidor.name
    )


    print(
        servidor.url
    )



    nombre = servidor.name.lower()


    stream = None



    if "voe" in nombre:


        print(
            "\nExtrayendo Voe..."
        )


        stream = extract_voe(
            servidor.url
        )



    elif "yourupload" in nombre:


        print(
            "\nExtrayendo YourUpload..."
        )


        stream = extract_yourupload(
            servidor.url
        )



    else:


        print(
            "Servidor no soportado."
        )

        return



    if not stream:


        print(
            "No se pudo extraer el stream."
        )

        return



    print(
        "\n========== STREAM ==========\n"
    )


    if isinstance(stream, dict):

        print(
            stream["url"]
        )


        abrir_vlc(
            stream["url"],
            stream.get("referer")
        )


    else:

        print(
            stream
        )


        abrir_vlc(
            stream
        )





def main():


    query = input(
        "Buscar anime: "
    ).strip()



    resultados = search(query)



    if not resultados:

        print(
            "No se encontraron resultados."
        )

        return



    print()


    for i, anime in enumerate(
        resultados,
        start=1
    ):

        print(
            f"{i}. {anime.title}"
        )



    anime = resultados[
        elegir(
            len(resultados),
            "Anime: "
        ) - 1
    ]



    anime = get_anime(
        anime.slug
    )



    episodios = sorted(
        anime.episodes
    )



    while True:


        print(
            "\n========== CAPÍTULOS ==========\n"
        )


        for i, episodio in enumerate(
            episodios,
            start=1
        ):

            print(
                f"{i}. Episodio {episodio}"
            )



        print()



        episodio = elegir(
            len(episodios),
            "Capítulo: "
        )



        episodio = episodios[
            episodio - 1
        ]



        print(
            f"\nReproduciendo episodio {episodio}"
        )



        servidores = get_servers(
            anime.slug,
            episodio
        )



        if not servidores:

            print(
                "No hay servidores."
            )

            continue



        reproducir(
            servidores
        )



        while True:


            print(
                "\n========== OPCIONES =========="
            )

            print(
                "1. Cambiar capítulo"
            )

            print(
                "2. Repetir capítulo"
            )

            print(
                "3. Salir"
            )


            opcion = input(
                "\nOpción: "
            )



            if opcion == "1":

                break



            elif opcion == "2":

                reproducir(
                    servidores
                )



            elif opcion == "3":

                print(
                    "Saliendo..."
                )

                return



            else:

                print(
                    "Opción inválida."
                )





if __name__ == "__main__":

    main()