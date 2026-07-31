import os
import shutil
import subprocess
import platform


def is_wsl():
    try:
        return (
            platform.system() == "Linux"
            and (
                "microsoft" in platform.release().lower()
                or "microsoft" in open("/proc/version").read().lower()
            )
        )
    except Exception:
        return False


def is_termux():
    return os.path.exists("/data/data/com.termux")


def get_player():

    # Windows nativo
    if platform.system() == "Windows":

        posibles = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
        ]

        for p in posibles:
            if os.path.exists(p):
                return p, "vlc"

    # WSL
    if is_wsl():

        posibles = [
            "/mnt/c/Program Files/VideoLAN/VLC/vlc.exe",
            "/mnt/c/Program Files (x86)/VideoLAN/VLC/vlc.exe"
        ]

        for p in posibles:
            if os.path.exists(p):
                return p, "vlc"

        raise FileNotFoundError(
            "No encontré VLC de Windows."
        )

    # Termux
    if is_termux():

        mpv = shutil.which("mpv")

        if mpv:
            return mpv, "mpv"

        raise FileNotFoundError(
            "Instala mpv:\n\npkg install mpv"
        )

    # Linux normal
    vlc = shutil.which("vlc")

    if vlc:
        return vlc, "vlc"

    mpv = shutil.which("mpv")

    if mpv:
        return mpv, "mpv"

    raise FileNotFoundError(
        "No encontré VLC ni MPV instalados."
    )


def play(url, referer=None):

    reproductor, tipo = get_player()

    print("\n========== REPRODUCTOR ==========\n")
    print(tipo.upper())
    print(reproductor)

    if tipo == "vlc":

        comando = [reproductor]

        if referer:

            comando.extend([
                f":http-referrer={referer}",
                ":http-user-agent=Mozilla/5.0"
            ])

        comando.append(url)

    else:

        comando = [
            reproductor,
            "--force-window=yes",
            "--profile=fast",
            "--referrer=" + (referer or ""),
            "--user-agent=Mozilla/5.0",
            url
        ]

    print("\nAbriendo reproductor...\n")

    try:

        proceso = subprocess.Popen(comando)

        proceso.wait()

        print("\nReproductor cerrado.")

    except KeyboardInterrupt:

        try:
            proceso.terminate()
        except Exception:
            pass

    except Exception as e:

        print("\nError al abrir el reproductor:")
        print(e)