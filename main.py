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

        subprocess.Popen(
            comando
        )


        print(
            "VLC iniciado correctamente."
        )


    except Exception as e:

        print(
            "Error abriendo VLC:"
        )

        print(e)




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



    print()



    anime = resultados[
        elegir(
            len(resultados),
            "Anime: "
        ) - 1
    ]



    anime = get_anime(
        anime.slug
    )



    print(
        "\nCapítulos\n"
    )



    episodios = sorted(
        anime.episodes
    )



    for episodio in episodios:

        print(
            episodio
        )



    print()



    episodio = elegir(
        len(episodios),
        "Selecciona un episodio: "
    )



    episodio = episodios[
        episodio - 1
    ]



    servidores = get_servers(
        anime.slug,
        episodio
    )



    print(
        "\n========== SERVIDORES ==========\n"
    )



    for i, servidor in enumerate(
        servidores,
        start=1
    ):

        premium = (
            " (Premium)"
            if servidor.premium
            else ""
        )


        print(
            f"{i}. {servidor.name}{premium}"
        )


        print(
            f"   URL: {servidor.url}"
        )


        print()



    servidor = servidores[
        elegir(
            len(servidores),
            "Servidor: "
        ) - 1
    ]



    print(
        "\n========== SELECCIONADO ==========\n"
    )


    print(
        f"Servidor : {servidor.name}"
    )


    print(
        f"URL       : {servidor.url}"
    )



    stream = None



    nombre = servidor.name.lower()



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
            "\nServidor sin resolver todavía."
        )

        return




    if not stream:


        print(
            "\nNo se pudo extraer el stream."
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





if __name__ == "__main__":

    main()