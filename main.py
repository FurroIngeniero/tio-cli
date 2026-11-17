import os, sys, re, unicodedata, subprocess
import providers.tioanime as tioanime, providers.jkanime as jkanime
from library import (
    all_anime, get, update, sync_anime_status, remove,
    get_global_tags, create_global_tag, delete_global_tag, set_anime_tags
)
from player import play
from providers.resolvers import resolve

SLUG_MAP_JKANIME = {
    "high-school-dxd": "highschool-dxd",
    "high-school-dxd-new": "highschool-dxd-new",
    "high-school-dxd-born": "highschool-dxd-born",
    "high-school-dxd-hero": "highschool-dxd-hero",
    "ranma": "ranma-",
    "kusuriya-no-hitogoto": "kusuriya-no-hitorigoto",
    "kusuriya-no-hitorigoto": "kusuriya-no-hitorigoto",
    "kono-subarashii-sekai-ni-shukufuku-wo": "kono-subarashii-sekai-ni-shukufuku-wo",
    "kono-subarashii-sekai-ni-shukufuku-wo-2": "kono-subarashii-sekai-ni-shukufuku-wo-2",
    "kono-subarashii-sekai-ni-shukufuku-wo-3": "kono-subarashii-sekai-ni-shukufuku-wo-3",
}

def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")

def elegir(maximo, mensaje, minimo=1):
    while True:
        print()
        opcion = input(mensaje)
        if opcion.isdigit() and minimo <= int(opcion) <= maximo:
            return int(opcion)
        print(" ❌ Opción inválida. Intenta nuevamente.")

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
        r"\b2nd\b|\b3rd\b|\b4th\b|\b1st\b",
        r"\b\d+\b$"
    ]
    for p in patrones:
        n = re.sub(p, "", n, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", n).strip()

def son_titulos_similares(t1, t2):
    base1 = limpiar_temporadas_titulo(t1)
    base2 = limpiar_temporadas_titulo(t2)
    
    if not base1 or not base2: return False
    if base1 == base2:
        return True
        
    palabras1 = set(w for w in base1.split() if len(w) > 2)
    palabras2 = set(w for w in base2.split() if len(w) > 2)
    
    if not palabras1 or not palabras2: return False
        
    interseccion = palabras1.intersection(palabras2)
    union = palabras1.union(palabras2)
    
    # Usar similitud de Jaccard (>= 0.75) para evitar fusionar series distintas como "Black Jack" y "Young Black Jack"
    return len(union) > 0 and (len(interseccion) / len(union)) >= 0.75

def sufijo_ordinal(num):
    if num == 1: return "1st"
    if num == 2: return "2nd"
    if num == 3: return "3rd"
    return f"{num}th"

def extraer_base_y_temporada(slug):
    m = re.search(r"-(?:season-)?(\d+)(?:st|nd|rd|th)?(?:-season)?$", slug)
    if m:
        num = int(m.group(1))
        base = slug[:m.start()]
        return base, num
    return slug, None

def extraer_numero_temporada_texto(texto):
    t = normalizar_titulo(texto).replace("-", " ")
    patrones = [
        r"\bseason\s*(\d+)\b",
        r"\b(\d+)(?:st|nd|rd|th)?\s*season\b",
        r"\bs(\d+)\b",
        r"\bpart(?:e)?\s*(\d+)\b",
        r"\b(\d+)(?:st|nd|rd|th)?\s*part(?:e)?\b",
    ]
    for p in patrones:
        m = re.search(p, t)
        if m:
            return int(m.group(1))
    m_fin = re.search(r"\b(\d+)\s*$", t)
    if m_fin:
        num = int(m_fin.group(1))
        if 2 <= num <= 15:
            return num
    return 1

def generar_candidatos_temporada(slug_base, num_season):
    if num_season <= 1:
        return [slug_base]
    ord_str = sufijo_ordinal(num_season)
    return [
        f"{slug_base}-{ord_str}-season",
        f"{slug_base}-{num_season}",
        f"{slug_base}-season-{num_season}",
        f"{slug_base}-part-{num_season}",
    ]

def buscar_en_jkanime_robusto(query):
    resultados = []
    vistos = set()
    q_strip = query.strip()
    consultas = [q_strip, q_strip.replace(" ", "-"), q_strip.replace(" ", "")]
    limpia = limpiar_temporadas_titulo(query)
    if limpia:
        consultas.extend([limpia, limpia.replace(" ", "-")])

    for q in dict.fromkeys(consultas):
        if not q: continue
        try:
            for r in (jkanime.search(q) or []):
                if r.slug not in vistos:
                    vistos.add(r.slug)
                    resultados.append(r)
        except Exception:
            pass

    # Respaldo directo por slug exacto (ej. "black jack" -> "black-jack")
    slug_directo = re.sub(r"[^a-z0-9]+", "-", normalizar_titulo(q_strip)).strip("-")
    if slug_directo and slug_directo not in vistos:
        try:
            info_directa = jkanime.get_anime(slug_directo)
            if info_directa and info_directa.episodes:
                resultados.insert(0, info_directa)
        except Exception:
            pass

    return resultados

def buscar_slug_y_episodio_jkanime(slug_tio, anime_title, episodio=1):
    if slug_tio == "kono-subarashii-sekai-ni-shukufuku-wo":
        if episodio > 20:
            return "kono-subarashii-sekai-ni-shukufuku-wo-3", episodio - 20
        elif episodio > 10:
            if episodio == 11:
                return "kono-subarashii-sekai-ni-shukufuku-wo", 11
            return "kono-subarashii-sekai-ni-shukufuku-wo-2", episodio - 10
        else:
            return "kono-subarashii-sekai-ni-shukufuku-wo", episodio

    try:
        query_busqueda = limpiar_temporadas_titulo(anime_title)
        resultados_raw = buscar_en_jkanime_robusto(query_busqueda or anime_title)
        coincidencias = [res for res in resultados_raw if son_titulos_similares(anime_title, res.title)]

        slug_sin_temp, temp_detectada = extraer_base_y_temporada(slug_tio)
        slug_base_jk = SLUG_MAP_JKANIME.get(slug_sin_temp)

        if not slug_base_jk:
            t1_cands = [r for r in coincidencias if extraer_numero_temporada_texto(r.title) == 1 and extraer_numero_temporada_texto(r.slug) == 1]
            if t1_cands:
                slug_base_jk = sorted(t1_cands, key=lambda r: len(r.slug))[0].slug
            elif coincidencias:
                slug_base_jk = sorted(coincidencias, key=lambda r: len(r.slug))[0].slug
            else:
                slug_base_jk = SLUG_MAP_JKANIME.get(slug_tio, slug_tio)

        if temp_detectada and temp_detectada >= 2:
            for res in coincidencias:
                if extraer_numero_temporada_texto(res.title) == temp_detectada or extraer_numero_temporada_texto(res.slug) == temp_detectada:
                    return res.slug, episodio
            for cand in generar_candidatos_temporada(slug_base_jk, temp_detectada):
                test_info = jkanime.get_anime(cand)
                if test_info and test_info.episodes:
                    return cand, episodio

        temporadas_jk = {1: slug_base_jk}
        for res in coincidencias:
            num_t = max(
                extraer_numero_temporada_texto(res.title),
                extraer_numero_temporada_texto(res.slug)
            )
            if num_t >= 2 and num_t not in temporadas_jk:
                temporadas_jk[num_t] = res.slug

        ep_restante = episodio
        max_temp_conocida = max(temporadas_jk.keys())

        for season_idx in range(1, max(max_temp_conocida + 2, 10)):
            slug_actual = temporadas_jk.get(season_idx)
            info_temp = None

            if slug_actual:
                info_temp = jkanime.get_anime(slug_actual)
            else:
                for cand in generar_candidatos_temporada(slug_base_jk, season_idx):
                    test_info = jkanime.get_anime(cand)
                    if test_info and test_info.episodes:
                        slug_actual = cand
                        info_temp = test_info
                        temporadas_jk[season_idx] = cand
                        break

            if not slug_actual and season_idx > max_temp_conocida:
                break

            max_ep_temp = max(info_temp.episodes) if (info_temp and info_temp.episodes) else 0

            if season_idx < max_temp_conocida:
                if max_ep_temp in (12, 13, 24, 25, 26):
                    duracion_temp = max_ep_temp
                elif max_ep_temp > 13:
                    duracion_temp = 24
                else:
                    duracion_temp = 24 if ep_restante > 24 else 12

                if ep_restante > duracion_temp:
                    ep_restante -= duracion_temp
                    continue
                else:
                    return slug_actual or slug_base_jk, max(1, ep_restante)

            if slug_actual:
                limite = max_ep_temp if max_ep_temp > 0 else 24
                while ep_restante > limite and ep_restante > 24:
                    ep_restante -= 24
                return slug_actual, max(1, ep_restante)

        ultima_temp = max(temporadas_jk.keys())
        return temporadas_jk[ultima_temp], max(1, ep_restante)

    except Exception as e:
        print(f"\n ⚠️ Error buscando en JKAnime: {e}")
    return SLUG_MAP_JKANIME.get(slug_tio, slug_tio), episodio

def obtener_servidores_combinados(slug_tio, slug_jk, anime_title, episodio):
    print(f"\n ⏳ Obteniendo servidores para Cap. {episodio}...")
    servidores = []

    if slug_tio:
        slug_jk_resuelto, ep_jk = buscar_slug_y_episodio_jkanime(slug_tio, anime_title, episodio)
        if slug_jk and slug_jk != slug_tio and ep_jk == episodio:
            slug_jk_resuelto = slug_jk

        print(f" 🎯 Slug TioAnime : {slug_tio} (Cap. {episodio})")
        print(f" 🎯 Slug JKAnime  : {slug_jk_resuelto} (Cap. {ep_jk})\n")

        try:
            for s in (jkanime.get_servers(slug_jk_resuelto, ep_jk) or []):
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

    elif slug_jk:
        print(f" 🎯 Slug JKAnime  : {slug_jk} (Cap. {episodio})\n")
        try:
            for s in (jkanime.get_servers(slug_jk, episodio) or []):
                s.name = f"{s.name} (JKAnime)"
                servidores.append(s)
        except Exception as e:
            print(f" ⚠️ No se pudieron obtener servidores de JKAnime: {e}")

    return servidores

def reproducir(servidores):
    limpiar_pantalla()
    print("========================================")
    print("             SERVIDORES                 ")
    print("========================================\n")
    soportados = ("voe", "yourupload", "desu", "magi", "sw", "stape", "nika", "playmudos")
    filtrados, urls_vistas = [], set()

    for s in servidores:
        nom, url = s.name.lower(), s.url.lower()
        if "mega" in nom or "mega" in url or "mega.nz" in url: continue
        if any(p in nom for p in soportados) and s.url not in urls_vistas:
            urls_vistas.add(s.url)
            filtrados.append(s)

    if not filtrados:
        print(" ❌ No hay servidores reproducibles disponibles para este episodio.\n")
        input("\n Presiona Enter para continuar...")
        return False

    for i, s in enumerate(filtrados, 1):
        aviso_pc = " 💻 (Solo PC / No funciona en celular)" if "yourupload" in s.name.lower() else ""
        print(f" {i}. 🟢 {s.name}{aviso_pc}")
        
    print("\n 0. ↩️  Volver al menú de opciones")

    opcion = elegir(len(filtrados), "Selecciona un servidor: ", minimo=0)
    if opcion == 0: return False

    servidor = filtrados[opcion - 1]
    limpiar_pantalla()
    print("========================================")
    print(f" Reproduciendo: {servidor.name}")
    print("========================================\n")

    try:
        stream = resolve(servidor)
    except Exception as e:
        print(f" ❌ Error al extraer el stream: {e}")
        input("\n Presiona Enter para continuar...")
        return False

    if not stream:
        print(" ❌ No se pudo extraer el stream.")
        input("\n Presiona Enter para continuar...")
        return False

    url = stream["url"] if isinstance(stream, dict) else stream
    ref = stream.get("referer") if isinstance(stream, dict) else None
    play(url, ref) if ref else play(url)
    return True

def menu_asignar_etiquetas_anime(anime_slug, anime_title):
    while True:
        limpiar_pantalla()
        global_tags = get_global_tags()
        data = get(anime_slug) or {}
        tags_asignadas = set(data.get("tags", []))

        print("========================================")
        print(f" ASIGNAR ETIQUETAS: {anime_title}")
        print("========================================\n")
        
        if global_tags:
            print(" Marca/desmarca las etiquetas para este anime:\n")
            for i, tag in enumerate(global_tags, 1):
                check = "[x]" if tag in tags_asignadas else "[ ]"
                print(f" {i}. {check} {tag}")
            print("\n ➕  Escribe '+' para crear una nueva etiqueta rápidamente.")
        else:
            print(" 📭 Aún no tienes ninguna etiqueta creada en el sistema.")
            print("\n ➕  Escribe '+' para crear tu primera etiqueta.")

        print("\n 💡 Opciones:")
        print("    - Números separados por coma para marcar/desmarcar (ej: 1, 3)")
        print("    - '+' para crear y asignar una nueva etiqueta (ej: + Favoritos)")
        print("    - '0' o Enter para guardar y salir")

        raw = input("\n Opción(es): ").strip()

        if raw == "0" or not raw:
            set_anime_tags(anime_slug, list(tags_asignadas))
            break

        if raw == "+" or raw.startswith("+"):
            nombre_nueva = raw[1:].strip()
            if not nombre_nueva:
                nombre_nueva = input("\n 🏷️ Nombre de la nueva etiqueta: ").strip()

            if nombre_nueva:
                create_global_tag(nombre_nueva)
                tag_formateada = nombre_nueva.strip().title()
                
                tags_asignadas.add(tag_formateada)
                set_anime_tags(anime_slug, list(tags_asignadas))
            continue

        partes = [p.strip() for p in raw.split(",") if p.strip().isdigit()]
        if partes:
            for p in partes:
                idx = int(p) - 1
                if 0 <= idx < len(global_tags):
                    tag_sel = global_tags[idx]
                    if tag_sel in tags_asignadas:
                        tags_asignadas.remove(tag_sel)
                    else:
                        tags_asignadas.add(tag_sel)

            set_anime_tags(anime_slug, list(tags_asignadas))

def ciclo_reproduccion(slug_tio, slug_jk, anime_title, episodios, ep_inicial=None, is_completed=True):
    slug_principal = slug_tio or slug_jk
    episodio = ep_inicial
    total_eps = max(episodios) if episodios else 0

    while True:
        limpiar_pantalla()
        if episodio is None:
            print("========================================")
            print("             CAPÍTULOS                  ")
            print("========================================\n")
            for i, ep in enumerate(episodios, 1): print(f" {i}. Episodio {ep}")
            print("\n 0. ↩️  Volver atrás")
            idx = elegir(len(episodios), "Selecciona un capítulo: ", minimo=0)
            if idx == 0: return "BACK"
            episodio = episodios[idx - 1]

        print(f"\n ⏳ Cargando episodio {episodio} de {total_eps}...")
        
        es_final = (episodio == total_eps) and is_completed
        if es_final:
            print(" 📌 ¡Atención! Estás en el último capítulo de este anime.")

        update(slug_principal, anime_title, episodio, total_episodes=total_eps, is_completed=is_completed)
        servidores = obtener_servidores_combinados(slug_tio, slug_jk, anime_title, episodio)

        if not servidores:
            print(" ❌ No hay servidores disponibles para este capítulo.")
            input("\n Presiona Enter para continuar...")
            episodio = None
            continue

        reproducir(servidores)

        while True:
            limpiar_pantalla()
            print("========================================")
            print("              OPCIONES                  ")
            print("========================================\n")
            print(" 1. ▶️  Siguiente capítulo")
            print(" 2. ◀️  Capítulo anterior")
            print(" 3. 📋 Elegir capítulo")
            print(" 4. 🔄 Repetir capítulo")
            print(" 5. 🟢 Cambiar servidor")
            print(" 6. 🏷️  Asignar / Gestionar etiquetas de este anime")
            print(" 0. ↩️  Volver al menú principal")

            opcion = elegir(6, "Selecciona una opción: ", minimo=0)

            pos = episodios.index(episodio)
            if opcion == 1:
                if pos < len(episodios) - 1: episodio = episodios[pos + 1]
                else: 
                    print("\n 🔔 Ya estás en el último capítulo disponible.")
                    input("\n Presiona Enter para continuar...")
                break
            elif opcion == 2:
                if pos > 0: episodio = episodios[pos - 1]
                else: 
                    print("\n 🔔 Ya estás en el primer capítulo.")
                    input("\n Presiona Enter para continuar...")
                break
            elif opcion in (3, 4, 5):
                if opcion == 3: episodio = None
                break
            elif opcion == 6:
                menu_asignar_etiquetas_anime(slug_principal, anime_title)
            elif opcion == 0:
                return "MENU"

def obtener_episodios_unificados(seleccion):
    eps = set()
    is_completed = True

    if seleccion.get("slug_tio"):
        a_tio = tioanime.get_anime(seleccion["slug_tio"])
        if a_tio and a_tio.episodes:
            eps.update(a_tio.episodes)
            is_completed = getattr(a_tio, "is_completed", True)

    if seleccion.get("slug_jk"):
        slug_actual = seleccion["slug_jk"]
        slug_base_limpio, temp_inicial = extraer_base_y_temporada(slug_actual)
        season_idx = temp_inicial or 1

        while slug_actual:
            a_jk = jkanime.get_anime(slug_actual)
            if not a_jk or not a_jk.episodes: break
            offset = max(eps) if eps else 0
            if offset > 0 and min(a_jk.episodes) == 1 and max(a_jk.episodes) <= offset:
                eps.update([e + offset for e in a_jk.episodes])
            else:
                eps.update(a_jk.episodes)

            is_completed = getattr(a_jk, "is_completed", True)
            if is_completed and not temp_inicial and not seleccion.get("slug_tio"):
                break
            elif is_completed and not temp_inicial:
                season_idx += 1
                candidatos = generar_candidatos_temporada(slug_base_limpio, season_idx)
                encontrado = False
                for cand in candidatos:
                    siguiente_info = jkanime.get_anime(cand)
                    if siguiente_info and siguiente_info.episodes:
                        slug_actual = cand
                        encontrado = True
                        break
                if not encontrado:
                    break
            else:
                break

    lista_eps = sorted(list(eps)) if eps else []
    return lista_eps, is_completed

def verificar_nuevos_capitulos():
    animes = all_anime()
    en_emision = [a for a in animes if not a.get("is_completed", True)]
    if not en_emision:
        return

    print(" ⏳ Comprobando nuevos capítulos de series en emisión...")
    for a in en_emision:
        slug = a["slug"]
        info = tioanime.get_anime(slug) or jkanime.get_anime(slug)
        if info and info.episodes:
            nuevo_total = max(info.episodes)
            estado_final = getattr(info, "is_completed", False)
            if nuevo_total > a.get("total_episodes", 0) or estado_final != a.get("is_completed", False):
                sync_anime_status(slug, nuevo_total, estado_final)

def opciones_anime_seleccionado(slug_tio, slug_jk, title, episodios, is_completed=True):
    slug_principal = slug_tio or slug_jk
    while True:
        limpiar_pantalla()
        progreso = get(slug_principal)
        ep_visto = progreso.get("episode") if progreso else None
        tags = progreso.get("tags", []) if progreso else []
        
        print("========================================")
        print(f" ANIME: {title}")
        print("========================================\n")
        if ep_visto and episodios:
            print(f" 📍 Progreso actual: Capítulo {ep_visto} / {max(episodios)}")
        print(f" 🏷️  Etiquetas: {', '.join(tags) if tags else 'Ninguna'}")
        
        print("\n 1. ▶️  Ver capítulos / Reproducir")
        print(" 2. 🏷️  Asignar / Crear etiquetas")
        print(" 3. 🗑️  Borrar anime de mi lista")
        print(" 0. ↩️  Volver atrás")

        op = elegir(3, "Selecciona una opción: ", minimo=0)
        if op == 0:
            break
        elif op == 1:
            ep_inicial = None
            if ep_visto:
                limpiar_pantalla()
                print("========================================")
                print(f" CONTINUAR: {title}")
                print("========================================\n")
                print(" 1. Continuar desde el último capítulo visto")
                print(" 2. Elegir un capítulo específico")
                print(" 0. Cancelar")
                sub_op = elegir(2, "Opción: ", minimo=0)
                if sub_op == 0: continue
                if sub_op == 1: ep_inicial = ep_visto

            res = ciclo_reproduccion(slug_tio, slug_jk, title, episodios, ep_inicial, is_completed)
            if res == "MENU": break
        elif op == 2:
            menu_asignar_etiquetas_anime(slug_principal, title)
        elif op == 3:
            confirmar = input(f"\n ⚠️ ¿Estás seguro de que deseas eliminar '{title}' de tu lista? (s/N): ").strip().lower()
            if confirmar == 's':
                remove(slug_principal)
                print(f"\n 🗑️ '{title}' ha sido eliminado de tu historial y listas.")
                input("\n Presiona Enter para continuar...")
                break

def buscar_anime():
    limpiar_pantalla()
    query = input("\n 🔍 Buscar anime (o presiona Enter para cancelar): ").strip()
    if not query: return
    print("\n ⏳ Buscando resultados en TioAnime y JKAnime...\n")
    
    resultados_agrupados = []

    try:
        res_tio = tioanime.search(query) or []
        for a in res_tio:
            resultados_agrupados.append({
                "title": a.title, "providers": ["TioAnime"], "slug_tio": a.slug, "slug_jk": None
            })
    except Exception as e:
        print(f" ⚠️ Error buscando en TioAnime: {e}")

    try:
        res_jk = buscar_en_jkanime_robusto(query)
        for a in res_jk:
            agregado = False
            for item in resultados_agrupados:
                t_item = extraer_numero_temporada_texto(item["title"])
                t_jk = extraer_numero_temporada_texto(a.title)
                if son_titulos_similares(a.title, item["title"]) and t_item == t_jk:
                    if "JKAnime" not in item["providers"]:
                        item["providers"].append("JKAnime")
                        item["slug_jk"] = a.slug
                    agregado = True
                    break
            if not agregado:
                resultados_agrupados.append({
                    "title": a.title, "providers": ["JKAnime"], "slug_tio": None, "slug_jk": a.slug
                })
    except Exception as e:
        print(f" ⚠️ Error buscando en JKAnime: {e}")

    if not resultados_agrupados:
        print(" ❌ No se encontraron resultados.")
        input("\n Presiona Enter para continuar...")
        return

    limpiar_pantalla()
    print("========================================")
    print("             RESULTADOS                 ")
    print("========================================\n")
    for i, item in enumerate(resultados_agrupados, 1):
        provs = item["providers"]
        tag = "[Ambas]" if len(provs) > 1 else f"[{provs[0]}]"
        print(f" {i}. {item['title']} {tag}")
    print("\n 0. ↩️  Volver al menú principal")

    opcion = elegir(len(resultados_agrupados), "Selecciona un anime: ", minimo=0)
    if opcion == 0: return

    seleccion = resultados_agrupados[opcion - 1]
    episodios, is_completed = obtener_episodios_unificados(seleccion)
    opciones_anime_seleccionado(
        seleccion["slug_tio"], seleccion["slug_jk"], seleccion["title"], episodios, is_completed
    )

def continuar(filtro_etiqueta=None, solo_completados=False):
    limpiar_pantalla()
    verificar_nuevos_capitulos()

    while True:
        limpiar_pantalla()
        viendo = all_anime()
        
        if solo_completados:
            viendo = [
                a for a in viendo 
                if (a.get("is_completed", True) and a.get("total_episodes", 0) > 0 and a.get("episode", 0) >= a.get("total_episodes", 0))
            ]
            titulo_seccion = "          ANIMES COMPLETADOS            "
            msg_vacio = " 📭 No tienes animes registrados como completados."
        elif filtro_etiqueta:
            viendo = [a for a in viendo if filtro_etiqueta in a.get("tags", [])]
            titulo_seccion = f"          ETIQUETA: {filtro_etiqueta.upper()}          "
            msg_vacio = f" 📭 No hay animes registrados bajo la etiqueta '{filtro_etiqueta}'."
        else:
            viendo = [
                a for a in viendo 
                if not (a.get("is_completed", True) and a.get("total_episodes", 0) > 0 and a.get("episode", 0) >= a.get("total_episodes", 0))
            ]
            titulo_seccion = "          CONTINUAR VIENDO              "
            msg_vacio = " 📭 No tienes animes pendientes por continuar."

        if not viendo:
            print(f"\n{msg_vacio}")
            input("\n Presiona Enter para continuar...")
            return

        print("========================================")
        print(titulo_seccion)
        print("========================================\n")

        for i, a in enumerate(viendo, 1):
            ep_visto = a.get("episode", 0)
            ep_totales = a.get("total_episodes", 0)
            is_completed = a.get("is_completed", True)
            tags = a.get("tags", [])
            tag_str = f" [{', '.join(tags)}]" if tags else ""

            estado_str = ""
            if ep_totales > 0:
                if not is_completed and ep_visto < ep_totales:
                    estado_str = f" 🆕 ¡Nuevos capítulos! ({ep_visto}/{ep_totales})"
                elif not is_completed and ep_visto >= ep_totales:
                    estado_str = f" ⏳ En emisión - Al día ({ep_visto}/{ep_totales})"
                elif is_completed and ep_visto >= ep_totales:
                    estado_str = f" 🏁 [Cap. Final: {ep_visto}]"
                else:
                    estado_str = f" ({ep_visto}/{ep_totales})"

            print(f" {i}. {a.get('title') or a['slug']}{tag_str}{estado_str}")

        print("\n 0. ↩️  Volver al menú principal")

        opcion = elegir(len(viendo), "Selecciona un anime: ", minimo=0)
        if opcion == 0: return

        anime_sel = viendo[opcion - 1]
        slug_guardado = anime_sel["slug"]
        
        slug_tio_real = None
        slug_jk_real = None
        anime_real = tioanime.get_anime(slug_guardado)
        if anime_real and anime_real.episodes:
            slug_tio_real = slug_guardado
        else:
            anime_real = jkanime.get_anime(slug_guardado)
            if anime_real and anime_real.episodes:
                slug_jk_real = slug_guardado

        if not anime_real:
            print(" ⚠️ No se pudo encontrar la información de este anime.")
            input("\n Presiona Enter para continuar...")
            return

        is_completed = getattr(anime_real, "is_completed", True)
        if anime_real.episodes:
            sync_anime_status(anime_real.slug, max(anime_real.episodes), is_completed)

        opciones_anime_seleccionado(
            slug_tio_real, slug_jk_real, anime_real.title, sorted(anime_real.episodes), is_completed
        )

def menu_gestionar_etiquetas_global():
    while True:
        limpiar_pantalla()
        tags = get_global_tags()
        print("========================================")
        print("         GESTIONAR ETIQUETAS            ")
        print("========================================\n")
        print(" 1. ➕ Crear nueva etiqueta")
        print(" 2. 🗑️  Eliminar una etiqueta existente")
        print(" 3. 📂 Filtrar animes por etiqueta")
        print(" 0. ↩️  Volver al menú principal")

        op = elegir(3, "Selecciona una opción: ", minimo=0)
        if op == 0:
            break
        elif op == 1:
            nueva = input("\n Nombre de la nueva etiqueta: ").strip()
            if nueva:
                create_global_tag(nueva)
                print(f" 🏷️ Etiqueta '{nueva}' creada con éxito.")
                input("\n Presiona Enter para continuar...")
        elif op == 2:
            if not tags:
                print(" 📭 No hay etiquetas registradas para eliminar.")
                input("\n Presiona Enter para continuar...")
                continue
            limpiar_pantalla()
            print("========================================")
            print("          ELIMINAR ETIQUETA             ")
            print("========================================\n")
            for i, t in enumerate(tags, 1):
                print(f" {i}. 🏷️  {t}")
            print("\n 0. Cancelar")
            idx = elegir(len(tags), "Selecciona la etiqueta a eliminar: ", minimo=0)
            if idx > 0:
                tag_del = tags[idx - 1]
                delete_global_tag(tag_del)
                print(f" 🗑️ Etiqueta '{tag_del}' eliminada.")
                input("\n Presiona Enter para continuar...")
        elif op == 3:
            if not tags:
                print(" 📭 No hay etiquetas creadas todavía.")
                input("\n Presiona Enter para continuar...")
                continue
            limpiar_pantalla()
            print("========================================")
            print("          SELECCIONA ETIQUETA           ")
            print("========================================\n")
            for i, t in enumerate(tags, 1):
                print(f" {i}. 🏷️  {t}")
            print("\n 0. Volver")
            idx = elegir(len(tags), "Selecciona una etiqueta: ", minimo=0)
            if idx > 0:
                continuar(filtro_etiqueta=tags[idx - 1])

def main():
    while True:
        limpiar_pantalla()
        print("========================================")
        print("               TIO-CLI                  ")
        print("========================================\n")
        print(" 1. ▶️  Continuar viendo")
        print(" 2. 🏁 Animes completados")
        print(" 3. 🔍 Buscar anime")
        print(" 4. 🏷️  Gestionar etiquetas")
        print(" 0. 🚪 Salir")

        opcion = elegir(4, "Selecciona una opción: ", minimo=0)
        if opcion == 1: continuar()
        elif opcion == 2: continuar(solo_completados=True)
        elif opcion == 3: buscar_anime()
        elif opcion == 4: menu_gestionar_etiquetas_global()
        elif opcion == 0:
            limpiar_pantalla()
            print("\n ¡Hasta luego!\n")
            break

if __name__ == "__main__":
    main()