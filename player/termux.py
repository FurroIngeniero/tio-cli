import subprocess

def play(stream, referer=None):
    if not referer:
        referer = "https://jkanime.net/"

    comando = [
        "am", "start",
        "--user", "0",
        "-a", "android.intent.action.VIEW",
        "-t", "application/vnd.apple.mpegurl",
        "-d", stream,
        
        # 1. Pasar Referer a reproductores Android (VLC/Just Player/MX Player)
        "-e", "build_headers", f"Referer: {referer}",
        "-e", "http-referrer", referer,
        
        # 2. Forzar User-Agent de navegador
        "-e", "user_agent", "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
        
        # 3. Intentar forzar reproductor específico si está disponible (Ej. VLC Android)
        # "-n", "org.videolan.vlc/.gui.video.VideoPlayerActivity"
    ]

    try:
        subprocess.run(comando)
    except Exception as e:
        print(f"Error al abrir la App en Termux: {e}")