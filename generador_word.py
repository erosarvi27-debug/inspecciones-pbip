import os
import re
import io
import json
import base64
import unicodedata
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
import db_cloud

MAX_FOTOS_WORD = 8

MAPA_PLANTILLAS = {
    "R01-004-21": ["Plantilla_R01_2.docx", "Plantilla_R01.docx"],
    "R03-004-21": ["Plantilla_R03.docx"],
    "R06-004-21": ["Plantilla_R06.docx"],
    "R07-004-21": ["Plantilla_R07.docx"],
    "R08-004-21": ["Plantilla_R08.docx"],
}


def normalizar_texto(txt: str) -> str:
    """Limpia tildes, signos y espacios para emparejar descripciones con exactitud."""
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("ASCII")
    txt = re.sub(r"[^a-zA-Z0-9]", "", txt).lower()
    return txt


def insertar_parrafo_antes(parrafo_referencia):
    return parrafo_referencia.insert_paragraph_before()


def aplicar_marco_negro_1pt(inline_shape):
    """
    Aplica marco rectangular negro (#000000) de 1 pt (12700 EMUs),
    línea sólida con esquinas rectas, sin efectos y sin diseños de imagen.
    """
    inline = inline_shape._inline
    spPr = inline.find(".//" + qn("pic:spPr"))
    if spPr is None:
        return

    # Limpiar posibles bordes o efectos previos
    for tag in ("a:ln", "a:effectLst", "a:scene3d", "a:sp3d"):
        existente = spPr.find(qn(tag))
        if existente is not None:
            spPr.remove(existente)

    # Borde sólido negro de 1 pt (1 pt = 12700 EMUs) con esquinas rectas
    ln_xml = (
        f'<a:ln {nsdecls("a")} w="12700" cap="flat" cmpd="sng" algn="ctr">'
        f'  <a:solidFill><a:srgbClr val="000000"/></a:solidFill>'
        f'  <a:prstDash val="solid"/>'
        f'  <a:miter lim="800000"/>'
        f'</a:ln>'
    )
    spPr.append(parse_xml(ln_xml))

    # Lista de efectos vacía (sin sombra, sin reflejo, sin iluminado, sin 3D)
    spPr.append(parse_xml(f'<a:effectLst {nsdecls("a")}/>'))

    # Margen de extensión de 1 pt para que Word no recorte ninguno de los 4 bordes
    effect_extent = inline.find(qn("wp:effectExtent"))
    if effect_extent is not None:
        effect_extent.set("l", "12700")
        effect_extent.set("t", "12700")
        effect_extent.set("r", "12700")
        effect_extent.set("b", "12700")


def resolver_ruta_plantilla(codigo_formato: str) -> str:
    candidatos = MAPA_PLANTILLAS.get(codigo_formato, ["Plantilla_R01_2.docx", "Plantilla_R01.docx"])
    for nombre in candidatos:
        ruta = os.path.join("plantillas_oficiales", nombre)
        if os.path.exists(ruta):
            return ruta
    raise FileNotFoundError(f"No se encontró la plantilla para {codigo_formato} en 'plantillas_oficiales/'.")


def reemplazar_fecha_documento(doc, fecha_val: str):
    """Reemplaza FECHA: {{FECHA}} o FECHA: en párrafos y tablas de todas las hojas."""
    for p in doc.paragraphs:
        if "FECHA" in p.text.upper():
            p.text = f"FECHA: {fecha_val}"
            if p.runs:
                p.runs[0].font.bold = True
                p.runs[0].font.name = "Arial Narrow"
                p.runs[0].font.size = Pt(10)

    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if "{{FECHA}}" in p.text or "FECHA:" in p.text.upper():
                        p.text = f"FECHA: {fecha_val}"
                        if p.runs:
                            p.runs[0].font.bold = True
                            p.runs[0].font.name = "Arial Narrow"
                            p.runs[0].font.size = Pt(10)


def extraer_lista_fotos(f1_col, f2_col, fotos_json_col) -> list:
    """Obtiene hasta 8 imágenes en Base64 desde fotos_json o desde foto_1/foto_2 (folios antiguos)."""
    if fotos_json_col and fotos_json_col.get("type") != "null":
        val_json = fotos_json_col.get("value")
        if val_json:
            try:
                lista = json.loads(val_json)
                if isinstance(lista, list):
                    return [x for x in lista if x][:MAX_FOTOS_WORD]
            except Exception:
                pass

    fotos_legacy = []
    if f1_col and f1_col.get("type") != "null" and f1_col.get("value"):
        fotos_legacy.append(f1_col["value"])
    if f2_col and f2_col.get("type") != "null" and f2_col.get("value"):
        fotos_legacy.append(f2_col["value"])
    return fotos_legacy[:MAX_FOTOS_WORD]


def generar_desde_plantilla(inspeccion_id: int) -> str:
    # 1. Consultar Cabecera
    sql_cab = f"SELECT codigo_formato, fecha_inspeccion, responsable_inspeccion, turno, observacion_general FROM inspecciones_cabecera WHERE id = {inspeccion_id};"
    res_cab = db_cloud.ejecutar_sql(sql_cab)
    if not res_cab.get("rows"):
        raise ValueError(f"No existe la inspección con Folio ID {inspeccion_id}")

    fila_cab = res_cab["rows"][0]
    codigo_formato = str(fila_cab[0]["value"] or "R01-004-21").strip()
    fecha_raw = str(fila_cab[1]["value"] or "")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_raw):
        p_f = fecha_raw.split("-")
        fecha_val = f"{p_f[2]}/{p_f[1]}/{p_f[0]}"
    else:
        fecha_val = fecha_raw
    obs_general = str(fila_cab[4]["value"] or "Sin observaciones.")

    # 2. Consultar Detalles (incluyendo fotos_json)
    sql_det = f"""
    SELECT item_nro, equipo_elemento, estado_operativo, observacion_item, foto_1, foto_2, fotos_json
    FROM inspecciones_detalle
    WHERE cabecera_id = {inspeccion_id}
    ORDER BY item_nro ASC;
    """
    res_det = db_cloud.ejecutar_sql(sql_det)
    filas_det = res_det.get("rows", [])

    datos_items = {}
    lista_items_ordenados = []
    for f in filas_det:
        num_it = int(f[0]["value"])
        lista_fotos = extraer_lista_fotos(f[4], f[5], f[6] if len(f) > 6 else None)
        item_obj = {
            "item": num_it,
            "equipo": str(f[1]["value"] or "").strip(),
            "norm": normalizar_texto(str(f[1]["value"] or "")),
            "estado": str(f[2]["value"] or "").strip(),
            "obs": str(f[3]["value"] or "").strip(),
            "fotos": lista_fotos
        }
        datos_items[num_it] = item_obj
        lista_items_ordenados.append(item_obj)

    # 3. Abrir plantilla correspondiente
    ruta_plantilla = resolver_ruta_plantilla(codigo_formato)
    doc = Document(ruta_plantilla)
    reemplazar_fecha_documento(doc, fecha_val)

    lista_observaciones_pie = []
    contador_obs = 1

    # =========================================================================
    # CASO A: FORMATO R01-004-21 (Tabla de 8 columnas con OP, INP, OBSERVACIONES)
    # =========================================================================
    if codigo_formato == "R01-004-21":
        for tbl in doc.tables:
            for fila in tbl.rows:
                celdas = fila.cells
                if len(celdas) < 6:
                    continue

                item_detectado = None
                for idx_c in range(min(4, len(celdas))):
                    texto_c = celdas[idx_c].text.strip()
                    if re.match(r"^([1-9]|[1-3][0-9]|4[0-3])$", texto_c):
                        item_detectado = int(texto_c)
                        break

                if item_detectado and item_detectado in datos_items:
                    info = datos_items[item_detectado]
                    estado = info["estado"]
                    obs_texto = info["obs"]
                    fotos = info["fotos"]

                    celda_op = celdas[-3]
                    celda_inp = celdas[-2]
                    celda_obs = celdas[-1]

                    celda_op.text = ""
                    celda_inp.text = ""
                    celda_obs.text = ""

                    if estado == "OP":
                        celda_op.text = "X"
                    else:
                        celda_inp.text = "X"

                    for c_marca in [celda_op, celda_inp]:
                        if c_marca.paragraphs:
                            p_m = c_marca.paragraphs[0]
                            p_m.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            if p_m.runs:
                                p_m.runs[0].font.bold = True
                                p_m.runs[0].font.name = "Arial Narrow"
                                p_m.runs[0].font.size = Pt(9.5)

                    if obs_texto or fotos:
                        p_obs_celda = celda_obs.paragraphs[0]
                        p_obs_celda.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        r1 = p_obs_celda.add_run("OBS ")
                        r1.font.bold = True
                        r1.font.name = "Arial Narrow"
                        r1.font.size = Pt(9)

                        r2 = p_obs_celda.add_run(f"({contador_obs})")
                        r2.font.bold = True
                        r2.font.name = "Arial Narrow"
                        r2.font.size = Pt(9)
                        r2.font.subscript = True

                        lista_observaciones_pie.append({
                            "correlativo": contador_obs,
                            "item": item_detectado,
                            "equipo": info["equipo"],
                            "detalle": obs_texto,
                            "fotos": fotos[:MAX_FOTOS_WORD]
                        })
                        contador_obs += 1

    # =========================================================================
    # CASO B: FORMATOS R03, R06, R07, R08 (5 columnas: Descripción | SI | NO | N/A | P/A)
    # =========================================================================
    else:
        mapa_col = {"SI": -4, "NO": -3, "N/A": -2, "P/A": -1}
        usados = set()

        for tbl in doc.tables:
            for fila in tbl.rows:
                celdas = fila.cells
                if len(celdas) < 5:
                    continue

                desc_celda = celdas[0].text.strip()
                norm_celda = normalizar_texto(desc_celda)

                if not norm_celda or norm_celda == "descripcion":
                    continue
                if "escalasoescaleras" in norm_celda:
                    continue
                if celdas[0]._tc == celdas[-1]._tc:
                    continue

                info_match = None
                for obj in lista_items_ordenados:
                    if obj["item"] in usados:
                        continue
                    if (obj["norm"][:25] in norm_celda) or (norm_celda[:25] in obj["norm"]):
                        info_match = obj
                        usados.add(obj["item"])
                        break

                if info_match:
                    estado = info_match["estado"]
                    obs_texto = info_match["obs"]
                    fotos = info_match["fotos"]

                    for idx_opt in [-4, -3, -2, -1]:
                        celdas[idx_opt].text = ""

                    col_destino = mapa_col.get(estado, -4)
                    celda_marca = celdas[col_destino]
                    p_m = celda_marca.paragraphs[0]
                    p_m.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    if obs_texto or fotos:
                        r_x = p_m.add_run("X ")
                        r_x.font.bold = True
                        r_x.font.name = "Arial Narrow"
                        r_x.font.size = Pt(8.5)

                        r_obs = p_m.add_run("OBS")
                        r_obs.font.bold = True
                        r_obs.font.name = "Arial Narrow"
                        r_obs.font.size = Pt(8)

                        r_sub = p_m.add_run(f"({contador_obs})")
                        r_sub.font.bold = True
                        r_sub.font.name = "Arial Narrow"
                        r_sub.font.size = Pt(8)
                        r_sub.font.subscript = True

                        lista_observaciones_pie.append({
                            "correlativo": contador_obs,
                            "item": info_match["item"],
                            "equipo": info_match["equipo"],
                            "detalle": obs_texto,
                            "fotos": fotos[:MAX_FOTOS_WORD]
                        })
                        contador_obs += 1
                    else:
                        r_x = p_m.add_run("X")
                        r_x.font.bold = True
                        r_x.font.name = "Arial Narrow"
                        r_x.font.size = Pt(9.5)

    # =========================================================================
    # 5. SECCIÓN INFERIOR: OBSERVACIONES, HASTA 8 FOTOS CON MARCO NEGRO 1 PT Y FIRMA
    # =========================================================================
    p_obs_titulo = None
    p_firma = None

    for p in doc.paragraphs:
        txt_up = p.text.upper()
        if "OBSERVACIONES:" in txt_up and p_obs_titulo is None:
            p_obs_titulo = p
        elif "FIRMA DE INSPECTOR" in txt_up and p_firma is None:
            p_firma = p

    if p_firma is not None:
        if p_obs_titulo is not None:
            borrar = False
            a_eliminar = []
            for p in doc.paragraphs:
                if p == p_obs_titulo:
                    borrar = True
                    continue
                if p == p_firma:
                    break
                if borrar:
                    a_eliminar.append(p)
            for p_del in a_eliminar:
                p_del._element.getparent().remove(p_del._element)

        if lista_observaciones_pie:
            for obs_data in lista_observaciones_pie:
                p_texto = insertar_parrafo_antes(p_firma)
                p_texto.paragraph_format.space_before = Pt(6)
                p_texto.paragraph_format.space_after = Pt(4)

                r_pref = p_texto.add_run("OBS ")
                r_pref.bold = True
                r_pref.font.name = "Arial Narrow"
                r_pref.font.size = Pt(10)

                r_sub_h2 = p_texto.add_run(f"({obs_data['correlativo']})")
                r_sub_h2.bold = True
                r_sub_h2.font.name = "Arial Narrow"
                r_sub_h2.font.size = Pt(10)
                r_sub_h2.font.subscript = True

                r_eq = p_texto.add_run(f" - Ítem {obs_data['item']} ({obs_data['equipo']}): ")
                r_eq.bold = True
                r_eq.font.name = "Arial Narrow"
                r_eq.font.size = Pt(10)

                r_det = p_texto.add_run(obs_data["detalle"])
                r_det.font.name = "Arial Narrow"
                r_det.font.size = Pt(10)

                # Inserta hasta 8 fotos centradas en pares (4.16 cm x 7.00 cm) con marco negro 1 pt
                fotos_obs = obs_data["fotos"][:MAX_FOTOS_WORD]
                for idx_par in range(0, len(fotos_obs), 2):
                    par_actual = fotos_obs[idx_par : idx_par + 2]
                    p_img = insertar_parrafo_antes(p_firma)
                    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_img.paragraph_format.space_before = Pt(5)
                    p_img.paragraph_format.space_after = Pt(7)

                    for pos_en_par, b64_str in enumerate(par_actual):
                        try:
                            img_bytes = base64.b64decode(b64_str)
                            img_stream = io.BytesIO(img_bytes)
                            run_img = p_img.add_run()
                            inline_shape = run_img.add_picture(
                                img_stream, width=Cm(7.0), height=Cm(4.16)
                            )
                            aplicar_marco_negro_1pt(inline_shape)

                            if pos_en_par == 0 and len(par_actual) == 2:
                                run_sep = p_img.add_run("    ")
                                run_sep.font.size = Pt(10)
                        except Exception as e_img:
                            print(f"Advertencia al insertar imagen: {e_img}")
        else:
            p_sin_obs = insertar_parrafo_antes(p_firma)
            p_sin_obs.paragraph_format.space_after = Pt(12)
            r_so = p_sin_obs.add_run(obs_general if obs_general else "Sin observaciones.")
            r_so.font.name = "Arial Narrow"
            r_so.font.size = Pt(10)

        p_firma.paragraph_format.space_before = Pt(24)

    salida_nombre = f"{codigo_formato}_Inspeccion_{inspeccion_id}.docx"
    doc.save(salida_nombre)
    return salida_nombre
