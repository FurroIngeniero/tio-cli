import subprocess

VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"


def play(stream, referer=None):

    comando = [
        VLC_PATH,
        stream
    ]

    if referer:

        comando.extend([
            f"--http-referrer={referer}",
            "--http-user-agent=Mozilla/5.0"
        ])

    subprocess.run(comando)