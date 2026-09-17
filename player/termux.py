import subprocess

def play(stream, referer=None):
    if not referer:
        referer = "https://jkanime.net/"

    # Headers formateados como array/mapa para compatibilidad total con MX Player y ExoPlayer
    headers = [
        "Referer", referer,
        "User-Agent", "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
    ]

    comando = [
        "am", "start",
        "--user", "0",
        "-a", "android.intent.action.VIEW",
        "-t", "application/vnd.apple.mpegurl",
        "-d", stream,
        
        # 1. Compatibilidad ExoPlayer / Just Player / MPV
        "-e", "build_headers", f"Referer: {referer}",
        
        # 2. Compatibilidad VLC Android
        "-e", "http-referrer", referer,
        
        # 3. Compatibilidad MX Player / MX Player Pro
        "--esa", "headers", ",".join(headers),
        
        # 4. User-Agent global
        "-e", "user_agent", "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
    ]

    try:
        # Popen evita que la consola de Termux se quede enganchada esperando a la App
        subprocess.Popen(comando)
    except Exception as e:
        print(f"Error al abrir la App en Termux: {e}")