import os
import sys

from . import mpv
from . import termux
from . import vlc


def es_termux():
    """Detecta si el script se está ejecutando en Android dentro de Termux."""
    return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")


def play(url, referer="https://jkanime.net/"):
    """
    Punto de entrada unificado para main.py.
    Selecciona automáticamente el reproductor según la plataforma activa.
    """
    # 1. ENTORNO ANDROID (TERMUX)
    if es_termux():
        return termux.play(url, referer)

    # 2. INTENTO CON MPV (Windows / WSL / Linux)
    # Solo ejecuta si mpv.py encuentra un ejecutable nativo/compatible con el SO actual
    if mpv.obtener_ruta_mpv() is not None:
        exito = mpv.play(url, referer)
        if exito:
            return True

    # 3. FALLBACK A VLC (Si MPV no está disponible o falló la reproducción)
    print("⚠️ MPV no disponible o no pudo abrir el enlace. Intentando con VLC...")
    return vlc.play(url, referer)