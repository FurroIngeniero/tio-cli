import os
import shutil
import subprocess
import sys
import time

def es_entorno_termux():
    """Detecta si la CLI se está ejecutando dentro de Termux en Android."""
    return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")


def obtener_ruta_mpv():
    raiz_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. ENTORNO WINDOWS
    if sys.platform.startswith("win"):
        ruta_bin_local = os.path.join(raiz_proyecto, "bin", "mpv.exe")
        if os.path.exists(ruta_bin_local):
            os.environ["PATH"] += os.path.pathsep + os.path.dirname(ruta_bin_local)
            return ruta_bin_local
        return shutil.which("mpv")

    # 2. ENTORNO LINUX / WSL / TERMUX
    return shutil.which("mpv")


def play_termux_external(url, referer):
    """
    Fallback para Termux: abre el video en un reproductor instalado 
    en Android (VLC, MX Player, etc.) enviando las cabeceras HTTP necesarias.
    """
    # Método A: Usando termux-open (abre la app por defecto de video en Android)
    if shutil.which("termux-open"):
        try:
            subprocess.run(["termux-open", url])
            return True
        except Exception:
            pass

    # Método B: Lanzando un Intent directo de Android
    if shutil.which("am"):
        cmd = [
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", url,
            "-t", "video/*",
            "-e", "http-header-fields", f"Referer: {referer}\r\nUser-Agent: Mozilla/5.0"
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    return False


def play(url, referer="https://jkanime.net/", max_retries=3):
    if not referer:
        referer = "https://jkanime.net/"

    mpv_path = obtener_ruta_mpv()

    # Si estamos en Termux y NO está instalado el paquete 'mpv', usamos el reproductor externo
    if es_entorno_termux() and not mpv_path:
        print("\n📱 Detectado entorno Termux: Abriendo reproductor de Android...")
        return play_termux_external(url, referer)

    if not mpv_path:
        print("\n❌ Error: No se encontró 'mpv'.")
        if es_entorno_termux():
            print("💡 Para reproducir de forma nativa en Termux ejecuta:\n   pkg install mpv termux-api\n")
        else:
            print("💡 Instala mpv en tu sistema o colócalo en la carpeta 'bin/'.\n")
        return False

    cmd = [
        mpv_path,
        # 1. ANTI-STALL Y TIMEOUT AGRESIVO (2s)
        "--demuxer-lavf-o=http_persistent=0",
        "--demuxer-lavf-o=reconnect=1",
        "--demuxer-lavf-o=reconnect_streamed=1",
        "--demuxer-lavf-o=reconnect_delay_max=2",
        "--demuxer-lavf-o=rw_timeout=2000000",
        "--demuxer-lavf-o=err_detect=ignore_err",
        "--demuxer-lavf-o=fflags=+discardcorrupt",
        
        # 2. BUFFER Y RECOVERY
        "--demuxer-max-bytes=10M",
        "--demuxer-max-back-bytes=5M",
        "--framedrop=decoder",
        
        # 3. CABECERAS HTTP
        f"--http-header-fields=Referer: {referer}",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        
        url
    ]

    intentos = 0
    while intentos < max_retries:
        intentos += 1
        proceso = subprocess.run(cmd)
        
        if proceso.returncode == 0:
            return True

        if intentos < max_retries:
            time.sleep(2)

    return False