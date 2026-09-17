import os
import shutil
import subprocess
import sys
import time

def obtener_ejecutable(nombre, rutas_defecto):
    """Busca un ejecutable en el PATH o en rutas conocidas."""
    ruta = shutil.which(nombre)
    if ruta:
        return ruta
    for r in rutas_defecto:
        if os.path.exists(r):
            return r
    return None

def play(url, referer="https://jkanime.net/", max_retries=3):
    if not referer:
        referer = "https://jkanime.net/"

    # 1. Localizar VLC
    rutas_vlc = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\VideoLAN\VLC\vlc.exe")
    ]
    vlc_path = obtener_ejecutable("vlc", rutas_vlc)

    # 2. Localizar FFmpeg
    rutas_ffmpeg = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.path.dirname(__file__), "..", "bin", "ffmpeg.exe")
    ]
    ffmpeg_path = obtener_ejecutable("ffmpeg", rutas_ffmpeg)

    if not vlc_path:
        print("\n❌ Error: No se encontró VLC instalado.")
        return False

    if not ffmpeg_path:
        print("\n❌ Error: Se requiere 'ffmpeg' para canalizar la red hacia VLC.")
        print("💡 Descarga ffmpeg.exe y colócalo en C:\\ffmpeg\\bin\\ o en la carpeta bin/ del proyecto.\n")
        return False

    # Comando FFmpeg: Gestiona las cabeceras HTTP y el Anti-Stall
    cmd_ffmpeg = [
        ffmpeg_path,
        "-headers", f"Referer: {referer}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n",
        "-rw_timeout", "2000000",       # Corta socket colgado a los 2s
        "-i", url,
        "-c", "copy",                   # Copia directa de video/audio (0% de CPU)
        "-f", "mpegts",
        "pipe:1"                        # Envía la salida a la tubería
    ]

    # Comando VLC: Lee los datos directamente desde la memoria
    cmd_vlc = [
        vlc_path,
        "--network-caching=1000",
        "--file-caching=1000",
        "fd://0"                        # Entrada por descriptor de archivo 0 (stdin)
    ]

    intentos = 0
    while intentos < max_retries:
        intentos += 1
        try:
            # Popen de FFmpeg canalizando su salida al proceso de VLC
            p_ffmpeg = subprocess.Popen(cmd_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p_vlc = subprocess.Popen(cmd_vlc, stdin=p_ffmpeg.stdout, stderr=subprocess.DEVNULL)

            # Espera a que el usuario cierre la ventana de VLC
            p_vlc.wait()
            p_ffmpeg.kill()
            return True

        except Exception as e:
            if intentos < max_retries:
                time.sleep(2)

    return False