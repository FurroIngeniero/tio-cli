import os
import shutil
import subprocess
import sys
import time

def obtener_ruta_mpv():
    r"""
    Prioriza el ejecutable 'mpv.exe' ubicado en la carpeta bin/ del proyecto
    (D:\Usuarios\Documents\tio-cli\bin\mpv.exe).
    """
    # 1. Obtener la carpeta raíz del proyecto (tio-cli/) a partir de este archivo
    raiz_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ruta_bin_local = os.path.join(raiz_proyecto, "bin", "mpv.exe")

    # 2. Comprobar si existe en tio-cli/bin/mpv.exe
    if os.path.exists(ruta_bin_local):
        # Añade la carpeta bin al PATH temporal de Python
        directorio = os.path.dirname(ruta_bin_local)
        os.environ["PATH"] += os.path.pathsep + directorio
        return ruta_bin_local

    # 3. Fallback: Buscar en el PATH global del sistema
    ruta_global = shutil.which("mpv")
    if ruta_global:
        return ruta_global

    return None


def play(url, referer="https://jkanime.net/", max_retries=3):
    if not referer:
        referer = "https://jkanime.net/"

    mpv_path = obtener_ruta_mpv()

    if not mpv_path:
        print("\n❌ Error: No se encontró 'mpv.exe' en la carpeta 'bin/'.")
        print(r"💡 Asegúrate de que el archivo existe en: D:\Usuarios\Documents\tio-cli\bin\mpv.exe" + "\n")
        return False

    cmd = [
        mpv_path,
        # 1. ANTI-STALL Y DESCONEXIÓN RÁPIDA (Timeout agresivo a los 2s)
        "--demuxer-lavf-o=http_persistent=0",
        "--demuxer-lavf-o=reconnect=1",
        "--demuxer-lavf-o=reconnect_streamed=1",
        "--demuxer-lavf-o=reconnect_delay_max=2",
        "--demuxer-lavf-o=rw_timeout=2000000",
        "--demuxer-lavf-o=err_detect=ignore_err",
        "--demuxer-lavf-o=fflags=+discardcorrupt",
        
        # 2. BUFFER UNIVERSAL Y DESCARTE DE FRAMES CORRUPTOS
        "--demuxer-max-bytes=10M",
        "--demuxer-max-back-bytes=5M",
        "--framedrop=decoder",
        
        # 3. CABECERAS REQUERIDAS POR NIKA / PLAYMUDOS
        f"--http-header-fields=Referer: {referer}",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        
        url
    ]

    intentos = 0
    while intentos < max_retries:
        intentos += 1
        proceso = subprocess.run(cmd)
        
        # Si el usuario cierra MPV normalmente (código 0), termina
        if proceso.returncode == 0:
            return True

        if intentos < max_retries:
            time.sleep(2)

    return False