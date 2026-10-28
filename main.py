import os, re, unicodedata, subprocess
import providers.tioanime as tioanime, providers.jkanime as jkanime
from library import all_anime, get, update
from player import play
from providers.resolvers import resolve

SLUG_MAP_JKANIME = {
    "high-school-dxd": "highschool-dxd",
    "high-school-dxd-new": "highschool-dxd-new",
    "high-school-dxd-born": "high-school-dxd-born",
    "high-school-dxd-hero": "highschool-dxd-hero",
    "ranma": "ranma-",
    "kusuriya-no-hitogoto": "kusuriya-no-hitorigoto",
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
    title = title.replace("hitogoto", "hitorigoto")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", title)).strip()

def limpiar_temporadas_titulo(title):
    n = normalizar_titulo(title).replace("-", " ")
    patrones = [
        r"\bseason\s*\d+\b",
        r"\b\d+(st|nd|rd|th)?\s*season\b",
        r"\bpart\s*\d+\b",
        r"\b\d+(st|nd|rd|th)?\s*part\b",
        r"\bs\d+\b",
        r"\b2nd\b|\b3rd\b|\b4th\b|\b1st\b"
    ]
    for p in patrones:
        n = re.sub(p, "", n, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", n).strip()

def son_titulos_similares(t1, t2):
    base1 = limpiar_temporadas_titulo(t1)
    base2 = limpiar_temporadas_titulo(t2)
    
    if not base1 or not base2: return False
    if base1 == base2 or base1 in base2 or base2 in base1:
        return True
        
    palabras1 = set(w for w in base1.split() if len(w) > 2)
    palabras2 = set(w for w in base2.split() if len(w) > 2)
    
    if not palabras1 or not palabras2: return False
        
    interseccion = palabras1.intersection(palabras2)
    min_len = min(len(palabras1), len(palabras2))
    
    return min_len > 0 and (len(interseccion) / min_len) >= 0.7

def buscar_slug_y_episodio_jkanime(slug_tio, anime_title, episodio=1):
    if slug_tio in SLUG_MAP_JKANIME:
        return SLUG_MAP_JKANIME[slug_tio], episodio

    try:
        query_busqueda = limpiar_temporadas_titulo(anime_title)
        resultados = jkanime.search(query_busqueda) or jkanime.search(anime_title)
        
        if not resultados:
            return slug_tio, episodio

        coincidencias = [res for res in resultados if son_titulos_similares(anime_title, res.title)]

        if not coincidencias:
            return slug_tio, episodio

        slug_base = coincidencias[0].slug
        info_base = jkanime.get_anime(slug_base)
        
        if info_base and info_base.episodes:
            max_ep_t1 = max(info_base.episodes)
            
            if episodio > max_ep_t1:
                num_season = (episodio - 1) // max_ep_t1 + 1
                ep_relativo = (episodio - 1) % max_ep_t1 + 1
                
                for res in coincidencias:
                    r_slug = res.slug.lower()
                    if f"season-{num_season}" in r_slug or f"season{num_season}" in r_slug or f"{num_season}nd-season" in r_slug or f"{num_season}rd-season" in r_slug:
                        print(f" 🔀 Redirigiendo a JKAnime [{res.title}] Cap. {ep_relativo}")
                        return res.slug, ep_relativo

                slug_construido = f"{slug_base}-season-{num_season}"
                print(f" 🔀 Intentando slug dinámico en JKAnime: {slug_construido} Cap. {ep_relativo}")
                return slug_construido, ep_relativo

        return coincidencias[0].slug, episodio
    except Exception as e:
        print(f" ⚠️ Error buscando en JKAnime: {e}")
    return slug_tio, episodio

def obtener_servidores_combinados(slug_tio, anime_title, episodio):
    print(f" ⏳ Obteniendo servidores para Cap. {episodio} (JKAnime + TioAnime)...")
    
    slug_jk, ep_jk = buscar_slug_y_episodio_jkanime(slug_tio, anime_title, episodio)
    
    print(f" 🎯 Slug TioAnime : {slug_tio} (Cap. {episodio})")
    print(f" 🎯 Slug JKAnime  : {slug_jk} (Cap. {ep_jk})")
    
    servidores = []

    try:
        for s in (jkanime.get_servers(slug_jk, ep_jk) or []):
            s.name = f"{s.name} (JKAnime)"
            servidores.append(s)
    except Exception as e:
        print(f" ⚠️ No se pudieron obtener servidores de JKAnime: {e}")

    try:
        for s in (tioanime.get_servers(slug_tio, episodio) or []):
            s.name = f"{s.name} (TioAnime)"
            servidores.append(s)
    except Exception as e:
        print(f" ⚠️ No se pudieron obtener servidores de TioAnime: {e}")

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

def obtener_episodios_unificados(seleccion):
    """
    Rastrea episodios navegando por las temporadas en JKAnime apoyándose
    en el estado ('is_completed') de la ficha.
    """
    eps = set()
    
    if seleccion.get("slug_tio"):
        a_tio = tioanime.get_anime(seleccion["slug_tio"])
        if a_tio and a_tio.episodes:
            eps.update(a_tio.episodes)

    if seleccion.get("slug_jk"):
        slug_actual = seleccion["slug_jk"]
        season_idx = 1
        
        while slug_actual:
            a_jk = jkanime.get_anime(slug_actual)
            if not a_jk or not a_jk.episodes:
                break
                
            offset = max(eps) if eps else 0
            if season_idx > 1:
                eps.update([e + offset for e in a_jk.episodes])
            else:
                eps.update(a_jk.episodes)

            # Si el anime está finalizado en esta ficha, probamos consultar la siguiente temporada
            if getattr(a_jk, "is_completed", True):
                season_idx += 1
                slug_base_limpio = re.sub(r"-(season-\d+|\d+nd-season|\d+rd-season|\d+th-season)$", "", slug_actual)
                slug_siguiente = f"{slug_base_limpio}-season-{season_idx}"
                
                # Probar si la ficha de la siguiente temporada existe realmente en JKAnime
                siguiente_info = jkanime.get_anime(slug_siguiente)
                if siguiente_info and siguiente_info.episodes:
                    slug_actual = slug_siguiente
                else:
                    break
            else:
                break

    return sorted(list(eps)) if eps else list(range(1, 13))

def buscar_anime():
    query = input("\nBuscar anime (o presiona Enter para cancelar): ").strip()
    if not query: return
    print(" ⏳ Buscando anime en TioAnime y JKAnime...")
    
    resultados_agrupados = []

    try:
        res_tio = tioanime.search(query) or []
        for a in res_tio:
            resultados_agrupados.append({
                "title": a.title,
                "providers": ["TioAnime"],
                "slug_tio": a.slug,
                "slug_jk": None
            })
    except Exception as e:
        print(f" ⚠️ Error buscando en TioAnime: {e}")

    try:
        res_jk = jkanime.search(query) or []
        for a in res_jk:
            agregado = False
            for item in resultados_agrupados:
                if son_titulos_similares(a.title, item["title"]):
                    if "JKAnime" not in item["providers"]:
                        item["providers"].append("JKAnime")
                        item["slug_jk"] = a.slug
                    agregado = True
                    break
            
            if not agregado:
                resultados_agrupados.append({
                    "title": a.title,
                    "providers": ["JKAnime"],
                    "slug_tio": None,
                    "slug_jk": a.slug
                })
    except Exception as e:
        print(f" ⚠️ Error buscando en JKAnime: {e}")

    if not resultados_agrupados:
        print("No se encontraron resultados en ningún proveedor.")
        return

    print("\n========== RESULTADOS ==========\n")
    for i, item in enumerate(resultados_agrupados, 1):
        provs = item["providers"]
        tag = "[Ambas]" if len(provs) > 1 else f"[{provs[0]}]"
        print(f"{i}. {item['title']} {tag}")
    print("0. ↩️  Volver al menú principal\n")

    opcion = elegir(len(resultados_agrupados), "Anime: ", minimo=0)
    if opcion == 0: return

    seleccion = resultados_agrupados[opcion - 1]
    
    episodios = obtener_episodios_unificados(seleccion)
    slug_principal = seleccion["slug_tio"] or seleccion["slug_jk"]
    titulo_principal = seleccion["title"]

    progreso = get(slug_principal)
    episodio = None

    if progreso:
        print(f"\n========== PROGRESO ==========\n\nÚltimo capítulo visto: {progreso['episode']}\n")
        print("1. Continuar\n2. Elegir capítulo\n0. Volver atrás")
        op = elegir(2, "Opción: ", minimo=0)
        if op == 0: return
        if op == 1: episodio = progreso["episode"]

    ciclo_reproduccion(slug_principal, titulo_principal, episodios, episodio)

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
        if not anime_real:
            anime_real = jkanime.get_anime(anime_sel["slug"])

        if not anime_real:
            print(" ⚠️ No se pudo encontrar la información de este anime.")
            return

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
