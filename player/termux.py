import subprocess


def play(stream, referer=None):

    print("\nAbriendo MPV para Android...")

    comando = [
        "am",
        "start",
        "-a",
        "android.intent.action.VIEW",
        "-d",
        stream,
        "-t",
        "video/*"
    ]

    try:
        subprocess.run(
            comando,
            check=True
        )

    except Exception as e:

        print("Error abriendo MPV:")
        print(e)