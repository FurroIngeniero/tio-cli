import os
import shutil
import subprocess

def obtener_ruta_vlc():
    """Busca el ejecutable de VLC en el PATH o en las rutas por defecto de Windows."""
    ruta = shutil.which("vlc")
    if ruta:
        return ruta

    rutas_comunes = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\VideoLAN\VLC\vlc.exe")
    ]

    for r in rutas_comunes:
        if os.path.exists(r):
            return r

    return None


def play(url, referer="https://jkanime.net/"):
    vlc_path = obtener_ruta_vlc()

    if not vlc_path:
        print("\n❌ Error: No se encontró VLC instalado en el sistema.\n")
        return

    if not referer:
        referer = "https://jkanime.net/"

    cmd = [
        vlc_path,
        # 1. Cabecera HTTP obligatoria
        f"--http-referrer={referer}",
        
        # 2. Desactiva la persistencia HTTP y reconecta en saltos de CDN (Equivalente a http_persistent=0)
        "--http-reconnect",
        "--sout-avformat-options={http_persistent=0}",
        
        # 3. Buffer de red (3 segundos evita congelamientos en HLS dinámico)
        "--network-caching=3000",
        
        url
    ]

    try:
        # Popen permite abrir la ventana de VLC sin congelar la terminal de Python
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"\n❌ Error al ejecutar VLC: {e}")