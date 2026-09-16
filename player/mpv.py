import subprocess

def play(url, referer="https://jkanime.net/"):
    if not referer:
        referer = "https://jkanime.net/"

    cmd = [
        "mpv",
        # 1. SOLUCIÓN AL ERROR: Desactiva Keep-Alive en FFmpeg para permitir cambio de CDN
        "--demuxer-lavf-o=http_persistent=0",
        
        # 2. Reconexión automática si el segmento .ts falla o cambia de host
        "--demuxer-lavf-o=reconnect=1",
        "--demuxer-lavf-o=reconnect_streamed=1",
        "--demuxer-lavf-o=reconnect_delay_max=5",
        
        # 3. Encabezados HTTP requeridos por Desu/Nika
        f"--http-header-fields=Referer: {referer}",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        
        # 4. Ajustes de Buffer para evitar congelamiento
        "--cache=yes",
        "--demuxer-max-bytes=50M",
        
        url
    ]

    try:
        # Usa Popen para abrir el reproductor sin bloquear la terminal
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"Error al ejecutar MPV: {e}")