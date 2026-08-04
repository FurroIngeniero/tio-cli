import shutil
import subprocess


def play(stream, referer=None):

    mpv = shutil.which("mpv")

    if not mpv:

        raise FileNotFoundError(
            "No se encontró MPV en el PATH."
        )

    comando = [

        mpv,

        "--force-window=yes",

        "--cache=yes",

        "--cache-secs=20",

        "--profile=fast"

    ]

    if referer:

        comando.append(
            f"--http-header-fields=Referer: {referer}"
        )

    if isinstance(stream, dict):

        comando.append(
            stream["url"]
        )

    else:

        comando.append(
            stream
        )

    print("\n========== MPV ==========\n")

    print("Comando:")

    print(" ".join(comando))

    subprocess.run(comando)