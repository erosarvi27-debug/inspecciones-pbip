import os
import re
import io
import base64
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import db_cloud

# Prioriza tu nueva plantilla Plantilla_R01_2.docx
PLANTILLA_PATH = os.path.join("plantillas_oficiales", "Plantilla_R01_2.docx")
if not os.path.exists(PLANTILLA_PATH):
    PLANTILLA_PATH = os.path.join("plantillas_oficiales", "Plantilla_R01.docx")

SALIDA_PATH = "R01_Equipos_Generado_Oficial.docx"


def insertar_parrafo_antes(parrafo_referencia):
    """Crea e inserta un nuevo párrafo exactamente encima de parrafo_referencia."""
    nuevo_p = parrafo_referencia.insert_paragraph_before()
    return nuevo_p


def generar_desde_plantilla(inspeccion_id: int):
    if not os.path.exists(PLANTILLA_PATH):
        raise FileNotFoundError(f"No se encontró la plantilla oficial en: {PLANTILLA_PATH}")

    # 1. Consultar cabecera en Turso Cloud
    sql_cab = f"SELECT fecha_inspeccion, responsable_inspeccion, turno, observacion_general FROM inspecciones_cabecera WHERE id = {inspeccion_id};"
    res_cab = db_cloud.ejecutar_sql(sql_cab)
    if not res_cab.get("rows"):
        raise ValueError(f"No existe la inspección con ID {inspeccion_id}")

    fila_cab = res_cab["rows"][0]
    fecha_raw = str(fila_cab[0]["value"] or "")
    # Formatear fecha YYYY-MM-DD a DD/MM/YYYY si viene en formato ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_raw):
        partes = fecha_raw.split("-")
        fecha_val = f"{partes[2]}/{partes[1]}/{partes[0]}"
    else:
        fecha_val = fecha_raw

    obs_general = str(fila_cab[3]["value"] or "")

    # 2. Consultar los 43 ítems (incluyendo foto_1 y foto_2)
    sql_det = f"""
    SELECT item_nro, equipo_elemento, estado_operativo, observacion_item, foto_1, foto_2 
    FROM inspecciones_detalle 
    WHERE cabecera_id = {inspeccion_id} 
    ORDER BY item_nro ASC;
    """
    res_det = db_cloud.ejecutar_sql(sql_det)
    filas_det = res_det.get("rows", [])

    datos_items = {}
    for f in filas_det:
        num_it = int(f[0]["value"])
        datos_items[num_it] = {
            "equipo": str(f[1]["value"] or "").strip(),
            "estado": str(f[2]["value"] or "OP").strip(),
            "obs": str(f[3]["value"] or "").strip(),
            "foto_1": f[4].get("value") if f[4].get("type") != "null" else None,
            "foto_2": f[5].get("value") if f[5].get("type") != "null" else None
        }

    # 3. Abrir plantilla oficial
    doc = Document(PLANTILLA_PATH)

    # Reemplazar FECHA en párrafos libres o en tablas
    for p in doc.paragraphs:
        if "FECHA:" in p.text.upper():
            p.text = f"FECHA: {fecha_val}"
            if p.runs:
                p.runs[0].font.bold = True
                p.runs[0].font.name = "Arial Narrow"
                p.runs[0].font.size = Pt(11)

    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if "FECHA:" in p.text.upper():
                        p.text = f"FECHA: {fecha_val}"
                        if p.runs:
                            p.runs[0].font.bold = True
                            p.runs[0].font.name = "Arial Narrow"
                            p.runs[0].font.size = Pt(10)

    # 4. Llenar la tabla de los 43 ítems (Hoja 1)
    lista_observaciones_hoja2 = []
    contador_obs = 1

    for tbl in doc.tables:
        for fila in tbl.rows:
            celdas = fila.cells
            if len(celdas) < 6:
                continue

            # Detectar número de ítem (1 al 43)
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
                f1 = info["foto_1"]
                f2 = info["foto_2"]

                celda_op = celdas[-3]
                celda_inp = celdas[-2]
                celda_obs = celdas[-1]

                celda_op.text = ""
                celda_inp.text = ""
                celda_obs.text = ""

                # Regla 1: Marcar X en OP o INP según corresponda
                if estado == "OP":
                    celda_op.text = "X"
                else:
                    celda_inp.text = "X"

                # Centrar la X en OP / INP
                for c_marca in [celda_op, celda_inp]:
                    if c_marca.paragraphs:
                        p_m = c_marca.paragraphs[0]
                        p_m.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        if p_m.runs:
                            p_m.runs[0].font.bold = True
                            p_m.runs[0].font.name = "Arial Narrow"
                            p_m.runs[0].font.size = Pt(9.5)

                # Regla 2: Si tiene observación (o fotos), colocar OBS (n) con (n) en subíndice
                if obs_texto or f1 or f2:
                    p_obs_celda = celda_obs.paragraphs[0]
                    p_obs_celda.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    run_obs = p_obs_celda.add_run("OBS ")
                    run_obs.font.bold = True
                    run_obs.font.name = "Arial Narrow"
                    run_obs.font.size = Pt(9)

                    run_sub = p_obs_celda.add_run(f"({contador_obs})")
                    run_sub.font.bold = True
                    run_sub.font.name = "Arial Narrow"
                    run_sub.font.size = Pt(9)
                    run_sub.font.subscript = True  # Subíndice oficial

                    lista_observaciones_hoja2.append({
                        "correlativo": contador_obs,
                        "item": item_detectado,
                        "equipo": info["equipo"],
                        "detalle": obs_texto,
                        "fotos": [f for f in [f1, f2] if f is not None]
                    })
                    contador_obs += 1

    # 5. Llenar las observaciones y fotos en la Hoja 2 (dejando FIRMA DE INSPECTOR intacta en blanco)
    p_obs_titulo = None
    p_firma = None

    for p in doc.paragraphs:
        txt_up = p.text.upper()
        if "OBSERVACIONES:" in txt_up and p_obs_titulo is None:
            p_obs_titulo = p
        elif "FIRMA DE INSPECTOR" in txt_up and p_firma is None:
            p_firma = p

    # Si la plantilla tiene FIRMA DE INSPECTOR, insertamos todo justo antes de esa línea
    # y dejamos FIRMA DE INSPECTOR completamente en blanco tal cual está.
    if p_firma is not None:
        # Limpiar posibles párrafos vacíos intermedios entre OBSERVACIONES: y FIRMA DE INSPECTOR:
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

        if lista_observaciones_hoja2:
            for obs_data in lista_observaciones_hoja2:
                # Regla 3: Detalle solo con Ítem y Equipo (sin marca ni serie)
                p_texto = insertar_parrafo_antes(p_firma)
                p_texto.paragraph_format.space_before = Pt(4)
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

                # Reglas 4 y 5: Hasta 2 fotos centradas de 4.16 cm de alto x 7.00 cm de ancho
                for b64_str in obs_data["fotos"][:2]:
                    try:
                        img_bytes = base64.b64decode(b64_str)
                        img_stream = io.BytesIO(img_bytes)

                        p_img = insertar_parrafo_antes(p_firma)
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.paragraph_format.space_before = Pt(4)
                        p_img.paragraph_format.space_after = Pt(6)

                        run_img = p_img.add_run()
                        run_img.add_picture(img_stream, width=Cm(7.0), height=Cm(4.16))
                    except Exception as e_img:
                        print(f"Advertencia al insertar imagen: {e_img}")
        else:
            p_sin_obs = insertar_parrafo_antes(p_firma)
            p_sin_obs.paragraph_format.space_after = Pt(12)
            r_so = p_sin_obs.add_run(obs_general if obs_general else "Sin observaciones.")
            r_so.font.name = "Arial Narrow"
            r_so.font.size = Pt(10)

        # Espaciado antes de FIRMA DE INSPECTOR: (sin alterar su texto en blanco)
        p_firma.paragraph_format.space_before = Pt(24)

    doc.save(SALIDA_PATH)
    print(f"✅ Documento oficial generado correctamente: {SALIDA_PATH}")
    return SALIDA_PATH


if __name__ == "__main__":
    # Prueba directa con el último folio
    res = db_cloud.ejecutar_sql("SELECT MAX(id) FROM inspecciones_cabecera;")
    ultimo_id = int(res["rows"][0][0]["value"]) if res.get("rows") else 1
    archivo = generar_desde_plantilla(inspeccion_id=ultimo_id)
    os.startfile(os.path.abspath(archivo))