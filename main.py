import os, re, unicodedata, subprocess
import providers.tioanime as tioanime, providers.jkanime as jkanime
from library import (
    all_anime, get, update, 
    get_global_tags, create_global_tag, delete_global_tag, set_anime_tags
)
from player import play
from providers.resolvers import resolve

SLUG_MAP_JKANIME = {
    "high-school-dxd": "highschool-dxd",
    "high-school-dxd-new": "highschool-dxd-new",
    "high-school-dxd-born": "high-school-dxd-born",
    "high-school-dxd-hero": "highschool-dxd-hero",
    "ranma": "ranma-",
    "kusuriya-no-hitogoto": "kusuriya-no-hitorigoto",
    "kono-subarashii-sekai-ni-shukufuku-wo": "kono-subarashii-sekai-ni-shukufuku-wo",
    "kono-subarashii-sekai-ni-shukufuku-wo-2": "kono-subarashii-sekai-ni-shukufuku-wo-2",
    "kono-subarashii-sekai-ni-shukufuku-wo-3": "kono-subarashii-sekai-ni-shukufuku-wo-3",
}

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
    if base1 == base2 or base1 in base2 or base2 in base1:
        return True
        
    palabras1 = set(w for w in base1.split() if len(w) > 2)
    palabras2 = set(w for w in base2.split() if len(w) > 2)
    
    if not palabras1 or not palabras2: return False
        
    interseccion = palabras1.intersection(palabras2)
    min_len = min(len(palabras1), len(palabras2))
    
    return min_len > 0 and (len(interseccion) / min_len) >= 0.7

def buscar_slug_y_episodio_jkanime(slug_tio, anime_title, episodio=1):
    if "kono-subarashii" in slug_tio or "konosuba" in slug_tio:
        if episodio > 20:
            return "kono-subarashii-sekai-ni-shukufuku-wo-3", episodio - 20
        elif episodio > 10:
            if episodio == 11:
                return "kono-subarashii-sekai-ni-shukufuku-wo", 11
            return "kono-subarashii-sekai-ni-shukufuku-wo-2", episodio - 10
        else:
            return "kono-subarashii-sekai-ni-shukufuku-wo", episodio

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
                if (episodio - max_ep_t1) <= 2:
                    return slug_base, episodio

                num_season = (episodio - 1) // max_ep_t1 + 1
                ep_relativo = (episodio - 1) % max_ep_t1 + 1
                
                for res in coincidencias:
                    r_slug = res.slug.lower()
                    if f"-{num_season}" in r_slug or f"season-{num_season}" in r_slug or f"{num_season}nd-season" in r_slug:
                        return res.slug, ep_relativo

                candidatos = [
                    f"{slug_base}-{num_season}",
                    f"{slug_base}-season-{num_season}",
                    f"{slug_base}-{num_season}nd-season"
                ]
                for cand in candidatos:
                    test_info = jkanime.get_anime(cand)
                    if test_info and test_info.episodes:
                        return cand, ep_relativo

        return coincidencias[0].slug, episodio
    except Exception as e:
        print(f"\n ⚠️ Error buscando en JKAnime: {e}")
    return slug_tio, episodio

def obtener_servidores_combinados(slug_tio, anime_title, episodio):
    print(f"\n ⏳ Obteniendo servidores para Cap. {episodio} (JKAnime + TioAnime)...")
    
    slug_jk, ep_jk = buscar_slug_y_episodio_jkanime(slug_tio, anime_title, episodio)
    
    print(f" 🎯 Slug TioAnime : {slug_tio} (Cap. {episodio})")
    print(f" 🎯 Slug JKAnime  : {slug_jk} (Cap. {ep_jk})\n")
    
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
    print("\n========================================")
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
        return False

    for i, s in enumerate(filtrados, 1):
        aviso_pc = " 💻 (Solo PC / No funciona en celular)" if "yourupload" in s.name.lower() else ""
        print(f" {i}. 🟢 {s.name}{aviso_pc}")
        
    print("\n 0. ↩️  Volver al menú de opciones")

    opcion = elegir(len(filtrados), "Selecciona un servidor: ", minimo=0)
    if opcion == 0: return False

    servidor = filtrados[opcion - 1]
    print("\n========================================")
    print(f" Reproduciendo: {servidor.name}")
    print("========================================\n")

    try:
        stream = resolve(servidor)
    except Exception as e:
        print(f" ❌ Error al extraer el stream: {e}")
        return False

    if not stream:
        print(" ❌ No se pudo extraer el stream.")
        return False

    url = stream["url"] if isinstance(stream, dict) else stream
    ref = stream.get("referer") if isinstance(stream, dict) else None
    play(url, ref) if ref else play(url)
    return True

def menu_asignar_etiquetas_anime(anime_slug, anime_title):
    while True:
        global_tags = get_global_tags()
        data = get(anime_slug) or {}
        tags_asignadas = set(data.get("tags", []))

        print("\n========================================")
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
            print("\n 🏷️  Etiquetas guardadas correctamente.")
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
                print(f"\n ✨ Etiqueta '{tag_formateada}' creada y asignada con éxito.")
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
            print("\n 🏷️  Cambios aplicados.")

def ciclo_reproduccion(anime_slug, anime_title, episodios, ep_inicial=None, is_completed=True):
    episodio = ep_inicial
    total_eps = max(episodios) if episodios else 0

    while True:
        if episodio is None:
            print("\n========================================")
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

        update(anime_slug, anime_title, episodio, total_episodes=total_eps, is_completed=is_completed)
        servidores = obtener_servidores_combinados(anime_slug, anime_title, episodio)

        if not servidores:
            print(" ❌ No hay servidores disponibles para este capítulo.")
            episodio = None
            continue

        reproducir(servidores)

        while True:
            print("\n========================================")
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
                else: print("\n 🔔 Ya estás en el último capítulo disponible.")
                break
            elif opcion == 2:
                if pos > 0: episodio = episodios[pos - 1]
                else: print("\n 🔔 Ya estás en el primer capítulo.")
                break
            elif opcion in (3, 4, 5):
                if opcion == 3: episodio = None
                break
            elif opcion == 6:
                menu_asignar_etiquetas_anime(anime_slug, anime_title)
            elif opcion == 0:
                return "MENU"

def obtener_episodios_unificados(seleccion):
    eps = set()
    is_completed = True

    if seleccion.get("slug_tio"):
        a_tio = tioanime.get_anime(seleccion["slug_tio"])
        if a_tio and a_tio.episodes: eps.update(a_tio.episodes)

    if seleccion.get("slug_jk"):
        slug_actual = seleccion["slug_jk"]
        season_idx = 1
        while slug_actual:
            a_jk = jkanime.get_anime(slug_actual)
            if not a_jk or not a_jk.episodes: break
            offset = max(eps) if eps else 0
            if season_idx > 1: eps.update([e + offset for e in a_jk.episodes])
            else: eps.update(a_jk.episodes)

            is_completed = getattr(a_jk, "is_completed", True)
            if is_completed:
                season_idx += 1
                slug_base_limpio = re.sub(r"-(season-\d+|\d+nd-season|\d+rd-season|\d+th-season|\d+)$", "", slug_actual)
                
                candidatos = [f"{slug_base_limpio}-{season_idx}", f"{slug_base_limpio}-season-{season_idx}"]
                encontrado = False
                for cand in candidatos:
                    siguiente_info = jkanime.get_anime(cand)
                    if siguiente_info and siguiente_info.episodes:
                        slug_actual = cand
                        encontrado = True
                        break
                if not encontrado:
                    break
            else: break

    lista_eps = sorted(list(eps)) if eps else []
    return lista_eps, is_completed

def opciones_anime_seleccionado(slug, title, episodios, is_completed=True):
    while True:
        progreso = get(slug)
        ep_visto = progreso.get("episode") if progreso else None
        tags = progreso.get("tags", []) if progreso else []
        
        print("\n========================================")
        print(f" ANIME: {title}")
        print("========================================\n")
        if ep_visto and episodios:
            print(f" 📍 Progreso actual: Capítulo {ep_visto} / {max(episodios)}")
        print(f" 🏷️  Etiquetas: {', '.join(tags) if tags else 'Ninguna'}")
        
        print("\n 1. ▶️  Ver capítulos / Reproducir")
        print(" 2. 🏷️  Asignar / Crear etiquetas")
        print(" 0. ↩️  Volver atrás")

        op = elegir(2, "Selecciona una opción: ", minimo=0)
        if op == 0:
            break
        elif op == 1:
            ep_inicial = None
            if ep_visto:
                print("\n 1. Continuar desde el último capítulo visto")
                print(" 2. Elegir un capítulo específico")
                print(" 0. Cancelar")
                sub_op = elegir(2, "Opción: ", minimo=0)
                if sub_op == 0: continue
                if sub_op == 1: ep_inicial = ep_visto

            res = ciclo_reproduccion(slug, title, episodios, ep_inicial, is_completed)
            if res == "MENU": break
        elif op == 2:
            menu_asignar_etiquetas_anime(slug, title)

def buscar_anime():
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
                    "title": a.title, "providers": ["JKAnime"], "slug_tio": None, "slug_jk": a.slug
                })
    except Exception as e:
        print(f" ⚠️ Error buscando en JKAnime: {e}")

    if not resultados_agrupados:
        print(" ❌ No se encontraron resultados.")
        return

    print("\n========================================")
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
    slug_principal = seleccion["slug_tio"] or seleccion["slug_jk"]
    titulo_principal = seleccion["title"]

    opciones_anime_seleccionado(slug_principal, titulo_principal, episodios, is_completed)

def continuar(filtro_etiqueta=None, solo_completados=False):
    while True:
        viendo = all_anime()
        
        if solo_completados:
            # Sección independiente: Mostrar únicamente los animes completados
            viendo = [
                a for a in viendo 
                if (a.get("is_completed", True) and a.get("total_episodes", 0) > 0 and a.get("episode", 0) >= a.get("total_episodes", 0)) 
                or "Completado" in a.get("tags", [])
            ]
            titulo_seccion = "          ANIMES COMPLETADOS            "
            msg_vacio = " 📭 No tienes animes registrados como completados."
        elif filtro_etiqueta:
            # Filtrado por etiqueta personalizada
            viendo = [a for a in viendo if filtro_etiqueta in a.get("tags", [])]
            titulo_seccion = f"          ETIQUETA: {filtro_etiqueta.upper()}          "
            msg_vacio = f" 📭 No hay animes registrados bajo la etiqueta '{filtro_etiqueta}'."
        else:
            # 'Continuar viendo': Oculta los animes finalizados que ya se completaron
            viendo = [
                a for a in viendo 
                if not (a.get("is_completed", True) and a.get("total_episodes", 0) > 0 and a.get("episode", 0) >= a.get("total_episodes", 0))
            ]
            titulo_seccion = "          CONTINUAR VIENDO              "
            msg_vacio = " 📭 No tienes animes pendientes por continuar."

        if not viendo:
            print(f"\n{msg_vacio}")
            return

        print("\n========================================")
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
                elif is_completed and ep_visto >= ep_totales:
                    estado_str = f" 🏁 [Cap. Final: {ep_visto}]"
                else:
                    estado_str = f" ({ep_visto}/{ep_totales})"

            print(f" {i}. {a.get('title') or a['slug']}{tag_str}{estado_str}")

        print("\n 0. ↩️  Volver al menú principal")

        opcion = elegir(len(viendo), "Selecciona un anime: ", minimo=0)
        if opcion == 0: return

        anime_sel = viendo[opcion - 1]
        
        anime_real = tioanime.get_anime(anime_sel["slug"])
        if not anime_real:
            anime_real = jkanime.get_anime(anime_sel["slug"])

        if not anime_real:
            print(" ⚠️ No se pudo encontrar la información de este anime.")
            return

        is_completed = getattr(anime_real, "is_completed", True)
        opciones_anime_seleccionado(anime_real.slug, anime_real.title, sorted(anime_real.episodes), is_completed)

def menu_gestionar_etiquetas_global():
    while True:
        tags = get_global_tags()
        print("\n========================================")
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
        elif op == 2:
            if not tags:
                print(" 📭 No hay etiquetas registradas para eliminar.")
                continue
            print("\n========================================")
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
        elif op == 3:
            if not tags:
                print(" 📭 No hay etiquetas creadas todavía.")
                continue
            print("\n========================================")
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
        print("\n========================================")
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
            print("\n ¡Hasta luego!\n")
            break

if __name__ == "__main__":
    main()