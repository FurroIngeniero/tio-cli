import os
import shutil
import subprocess
import sys
import time


def obtener_ruta_mpv():
    """Busca y valida la ruta de MPV según el sistema operativo actual."""
    raiz_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # --- 1. ENTORNO WINDOWS ---
    if sys.platform.startswith("win"):
        ruta_bin_local = os.path.join(raiz_proyecto, "bin", "mpv.exe")
        if os.path.exists(ruta_bin_local):
            directorio = os.path.dirname(ruta_bin_local)
            os.environ["PATH"] += os.path.pathsep + directorio
            return ruta_bin_local

        return shutil.which("mpv")

    # --- 2. ENTORNO LINUX / WSL / TERMUX ---
    # NUNCA se debe intentar ejecutar binarios .exe en sistemas POSIX
    ruta_linux = shutil.which("mpv")
    if ruta_linux:
        return ruta_linux

    # Fallback para un binario compilado o colocado en bin/ para Linux
    ruta_bin_nativa = os.path.join(raiz_proyecto, "bin", "mpv")
    if os.path.exists(ruta_bin_nativa) and os.access(ruta_bin_nativa, os.X_OK):
        return ruta_bin_nativa

    return None


def play(url, referer="https://jkanime.net/", max_retries=3):
    if not referer:
        referer = "https://jkanime.net/"

    mpv_path = obtener_ruta_mpv()

    if not mpv_path:
        # Retornamos False de forma limpia para permitir que player.py conmute a VLC
        return False

    cmd = [
        mpv_path,
        # 1. ANTI-STALL Y DESCONEXIÓN RÁPIDA (Timeout a los 2s)
        "--demuxer-lavf-o=http_persistent=0",
        "--demuxer-lavf-o=reconnect=1",
        "--demuxer-lavf-o=reconnect_streamed=1",
        "--demuxer-lavf-o=reconnect_delay_max=2",
        "--demuxer-lavf-o=rw_timeout=2000000",
        "--demuxer-lavf-o=err_detect=ignore_err",
        "--demuxer-lavf-o=fflags=+discardcorrupt",
        # 2. BUFFER UNIVERSAL Y RECOVER
        "--demuxer-max-bytes=10M",
        "--demuxer-max-back-bytes=5M",
        "--framedrop=decoder",
        # 3. CABECERAS HTTP PARA NIKA / PLAYMUDOS
        f"--http-header-fields=Referer: {referer}",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        url,
    ]

    intentos = 0
    while intentos < max_retries:
        intentos += 1
        try:
            proceso = subprocess.run(cmd)

            # Si el usuario cierra MPV normalmente (código 0), termina
            if proceso.returncode == 0:
                return True
        except Exception:
            return False

        if intentos < max_retries:
            time.sleep(2)

    return False