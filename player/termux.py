import subprocess


def play(stream, referer=None):

    comando = [
        "mpv",
        stream
    ]

    if referer:

        comando.extend([
            f"--http-header-fields=Referer: {referer}"
        ])

    subprocess.run(comando)