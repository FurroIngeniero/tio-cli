# 🎬 TIO-CLI

Una herramienta de línea de comandos ligera y eficiente escrita en Python para buscar, gestionar historial y reproducir episodios de anime directamente en tu reproductor local **MPV**, utilizando fuentes como **TioAnime** y **JKAnime** (como servidor de respaldo).

---

## 🚀 Características

- 🔍 **Búsqueda unificada:** Busca títulos de anime mediante la API/Scraping de TioAnime.
- 🔄 **Conmutación por error (Failover):** Si TioAnime falla o no devuelve resultados, el sistema alterna automáticamente a JKAnime.
- 📜 **Historial de actividad:** Guarda automáticamente tus últimas búsquedas y los episodios vistos recientemente en un archivo JSON local (`historial.json`).
- 📺 **Visualización mediante MPV:** Invocación directa del reproductor multimedia `mpv` para reproducir transmisiones sin abrir navegadores ni lidiar con publicidad.
- ⚡ **Interfaz interactiva:** Menú estructurado en consola mediante números para facilitar la navegación rápida.

---

## 🛠️ Requisitos Previos

Asegúrate de contar con las siguientes herramientas instaladas en tu sistema:

1. **Python 3.8+**
2. **MPV Player** (debe estar disponible en las variables de entorno / `PATH` del sistema).
   - *Linux:* `sudo apt install mpv` / `sudo pacman -S mpv`
   - *Windows:* Descargar de [mpv.io](https://mpv.io/) y agregar a las variables de entorno.
3. **yt-dlp** *(Recomendado)*: Permite a MPV procesar y extraer transmisiones desde los incrustados (iframes) de los reproductores.
   ```bash
   pip install yt-dlp


# 🎬 Instalacion


1. Clona el repositorio o descarga los archivos
2. Instala las dependencias de Python requiridas

# 💻 Uso

Ejecuta el script principal desde la terminal: 
  - Python main.py para Windows / Termux
  - python3 main.py para Linux


📄 Licencia

Este proyecto fue desarrollado para fines educativos y de entretenimiento personal. Siéntete libre de clonarlo, adaptarlo o contribuir con mejoras, cualquier intento de monetizacion con este proyecto queda estrictamente prohibido.
