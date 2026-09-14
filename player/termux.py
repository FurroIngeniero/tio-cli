import subprocess


def play(stream, referer=None):
    comando = [
        "am",
        "start",
        "--user", "0",
        "-a", "android.intent.action.VIEW",
        "-t", "application/vnd.apple.mpegurl",
        "-d", stream
    ]

    subprocess.run(comando)