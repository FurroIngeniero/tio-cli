import os
import shutil
import subprocess
import time

def play(url, referer="https://jkanime.net/"):
    if not referer:
        referer = "https://jkanime.net/"

    print("\n📱 [Termux] Abriendo reproducción en MPV para Android...")

    # Paquetes oficiales conocidos de MPV para Android
    paquetes_mpv = [
        "is.xyz.mpv",             # MPV oficial de Android (F-Droid / Play Store)
        "net.scriptbee.wmv",       # Distribución alternativa de MPV
        "org.videolan.vlc"         # VLC como alternativa inmediata
    ]

    # 1. INTENTO DIRECTO: Forzar el inicio de la app MPV especificando el paquete
    for paquete in paquetes_mpv:
        cmd_app = [
            "am", "start",
            "--user", "0",
            "-a", "android.intent.action.VIEW",
            "-d", url,
            "-t", "video/*",
            "-p", paquete,
            "-e", "http-header-fields", f"Referer: {referer}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ]
        
        proceso = subprocess.run(cmd_app, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proceso.returncode == 0:
            return True

    # 2. SI FALLA: Usar Intent tipo MIME video/* sin fijar navegador (Muestra "Abrir con...")
    cmd_mimetype = [
        "am", "start",
        "--user", "0",
        "-a", "android.intent.action.VIEW",
        "-setDataAndType", url, "video/*",
        "-e", "http-header-fields", f"Referer: {referer}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    ]
    
    proceso_mime = subprocess.run(cmd_mimetype, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proceso_mime.returncode == 0:
        return True

    # 3. ÚLTIMO RECURSO: Intent de Termux API
    if shutil.which("termux-open"):
        try:
            subprocess.run(["termux-open", "--content-type", "video/*", url])
            return True
        except Exception:
            pass

    print("❌ No se pudo abrir MPV. Asegúrate de tener instalada la App 'mpv' en tu Android.")
    return False