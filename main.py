import os, re, unicodedata, subprocess
import providers.tioanime as tioanime, providers.jkanime as jkanime
from library import all_anime, get, update
from player import play
from providers.resolvers import resolve

SLUG_MAP_JKANIME = {
    "high-school-dxd": "highschool-dxd", "high-school-dxd-new": "highschool-dxd-new",
    "high-school-dxd-born": "high-school-dxd-born", "high-school-dxd-hero": "highschool-dxd-hero",
    "ranma": "ranma-",
}

def elegir(maximo, mensaje, minimo=1):
    while True:
        opcion = input(mensaje)
        if opcion.isdigit() and minimo <= int(opcion) <= maximo:
            return int(opcion)
        print("Opción inválida." if opcion.isdigit() else "Ingresa un número válido.")

def normalizar_titulo(title):
    if not title: return ""
    title = title.lower().replace("½", "1 2").replace("⅓", "1 3").replace("⅔", "2 3")
    title = unicodedata.normalize('NFD', title).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", title)).strip()

def buscar_slug_jkanime(slug_tio, anime_title):
    if slug_tio in SLUG_MAP_JKANIME:
        print(f" 🔗 Mapeo JKAnime encontrado: {slug_tio} -> {SLUG_MAP_JKANIME[slug_tio]}")
        return SLUG_MAP_JKANIME[slug_tio]
    try:
        print(f" 🔎 Buscando '{anime_title}' en JKAnime...")
        resultados = jkanime.search(anime_title)
        if not resultados:
            print(" ⚠️ No se encontraron resultados en JKAnime.")
            return slug_tio
        
        target = normalizar_titulo(anime_title)
        for res in resultados:
            if normalizar_titulo(res.title) == target:
                print(f" ✅ Coincidencia exacta: {res.title} -> {res.slug}")
                return res.slug
        for res in resultados:
            res_t = normalizar_titulo(res.title)
            if target in res_t or res_t in target:
                print(f" ✅ Coincidencia aproximada: {res.title} -> {res.slug}")
                return res.slug
        print(f" ⚠️ No se encontró una coincidencia exacta para '{anime_title}' en JKAnime.")
    except Exception as e:
        print(f" ⚠️ Error buscando en JKAnime: {e}")
    return slug_tio

def obtener_servidores_combinados(slug_tio, anime_title, episodio):
    print(f" ⏳ Obteniendo servidores para Cap. {episodio} (JKAnime + TioAnime)...")
    slug_jk = buscar_slug_jkanime(slug_tio, anime_title)
    print(f" 🎯 Slug TioAnime : {slug_tio}\n 🎯 Slug JKAnime  : {slug_jk}")
    servidores = []
    
    for prov, slug, label in [(jkanime, slug_jk, "JKAnime"), (tioanime, slug_tio, "TioAnime")]:
        try:
            for s in (prov.get_servers(slug, episodio) or []):
                s.name = f"{s.name} ({label})"
                servidores.append(s)
        except Exception as e:
            print(f" ⚠️ No se pudieron obtener servidores de {label}: {e}")
    return servidores

def reproducir(servidores):
    print("\n========== SERVIDORES ==========\n")
    soportados = ("voe", "yourupload", "desu", "magi", "sw", "stape", "nika", "playmudos")
    filtrados, urls_vistas = [], set()

    for s in servidores:
        nom, url = s.name.lower(), s.url.lower()
        if "mega" in nom or "mega" in url or "mega.nz" in url: continue
        if any(p in nom for p in soportados) and s.url not in urls_vistas:
            urls_vistas.add(s.url)
            filtrados.append(s)

    if not filtrados:
        print("No hay servidores reproducibles disponibles para este episodio.\n")
        return False

    for i, s in enumerate(filtrados, 1): print(f"{i}. 🟢 {s.name}")
    print("0. ↩️  Volver al menú de opciones\n")

    opcion = elegir(len(filtrados), "Servidor: ", minimo=0)
    if opcion == 0: return False

    servidor = filtrados[opcion - 1]
    print(f"\n========== SERVIDOR ==========\n\n{servidor.name}\n{servidor.url}\n\nExtrayendo enlace de {servidor.name}...")

    try:
        stream = resolve(servidor)
    except Exception as e:
        print(f"\nError al extraer el stream: {e}")
        return False

    if not stream:
        print("\nNo se pudo extraer el stream.")
        return False

    print("\n========== REPRODUCIENDO ==========\n")
    url = stream["url"] if isinstance(stream, dict) else stream
    ref = stream.get("referer") if isinstance(stream, dict) else None
    print(url)
    play(url, ref) if ref else play(url)
    return True

def ciclo_reproduccion(anime_slug, anime_title, episodios, ep_inicial=None):
    episodio = ep_inicial
    while True:
        if episodio is None:
            print("\n========== CAPÍTULOS ==========\n")
            for i, ep in enumerate(episodios, 1): print(f"{i}. Episodio {ep}")
            print("0. ↩️  Volver atrás\n")
            idx = elegir(len(episodios), "Capítulo: ", minimo=0)
            if idx == 0: return "BACK"
            episodio = episodios[idx - 1]

        print(f"\nCargando episodio {episodio}...")
        update(anime_slug, anime_title, episodio)
        servidores = obtener_servidores_combinados(anime_slug, anime_title, episodio)

        if not servidores:
            print("No hay servidores disponibles.")
            episodio = None
            continue

        reproducir(servidores)

        while True:
            print("\n========== OPCIONES ==========\n")
            print("1. Siguiente capítulo\n2. Capítulo anterior\n3. Elegir capítulo\n4. Repetir capítulo\n5. Cambiar servidor\n0. ↩️  Volver al menú principal")
            opcion = elegir(5, "Opción: ", minimo=0)

            pos = episodios.index(episodio)
            if opcion == 1:
                if pos < len(episodios) - 1: episodio = episodios[pos + 1]
                else: print("Ya estás en el último capítulo.")
                break
            elif opcion == 2:
                if pos > 0: episodio = episodios[pos - 1]
                else: print("Ya estás en el primer capítulo.")
                break
            elif opcion in (3, 4, 5):
                if opcion == 3: episodio = None
                break
            elif opcion == 0:
                return "MENU"

def buscar_anime():
    query = input("\nBuscar anime (o presiona Enter para cancelar): ").strip()
    if not query: return
    print(" ⏳ Buscando anime...")
    resultados = tioanime.search(query)
    if not resultados:
        print("No se encontraron resultados.")
        return

    print("\n========== RESULTADOS ==========\n")
    for i, a in enumerate(resultados, 1): print(f"{i}. {a.title}")
    print("0. ↩️  Volver al menú principal\n")

    opcion = elegir(len(resultados), "Anime: ", minimo=0)
    if opcion == 0: return

    anime = tioanime.get_anime(resultados[opcion - 1].slug)
    progreso = get(anime.slug)
    episodios = sorted(anime.episodes)
    episodio = None

    if progreso:
        print(f"\n========== PROGRESO ==========\n\nÚltimo capítulo visto: {progreso['episode']}\n")
        print("1. Continuar\n2. Elegir capítulo\n0. Volver atrás")
        op = elegir(2, "Opción: ", minimo=0)
        if op == 0: return
        if op == 1: episodio = progreso["episode"]

    ciclo_reproduccion(anime.slug, anime.title, episodios, episodio)

def continuar():
    while True:
        viendo = all_anime()
        if not viendo:
            print("\nNo tienes animes en seguimiento.\n")
            return

        print("\n========== CONTINUAR VIENDO ==========\n")
        for i, a in enumerate(viendo, 1):
            print(f"{i}. {a['title'] or a['slug']} (Cap. {a['episode']})")
        print("0. ↩️  Volver al menú principal\n")

        opcion = elegir(len(viendo), "Anime: ", minimo=0)
        if opcion == 0: return

        anime_sel = viendo[opcion - 1]
        anime_real = tioanime.get_anime(anime_sel["slug"])
        res = ciclo_reproduccion(anime_real.slug, anime_real.title, sorted(anime_real.episodes), anime_sel["episode"])
        if res == "MENU": return

def main():
    while True:
        print("\n========== TIO-CLI ==========\n\n1. Continuar viendo\n2. Buscar anime\n0. Salir")
        opcion = elegir(2, "Opción: ", minimo=0)
        if opcion == 1: continuar()
        elif opcion == 2: buscar_anime()
        elif opcion == 0:
            print("¡Hasta luego!")
            break

if __name__ == "__main__":
    main()