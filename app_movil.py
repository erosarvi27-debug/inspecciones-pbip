import base64
import streamlit as st
from datetime import date
import db_cloud
import generador_word

st.set_page_config(page_title="R01 - Inspección PBIP", page_icon="🛡️", layout="centered")

# Asegurar que las columnas foto_1 y foto_2 existan en la nube
if "db_initialized" not in st.session_state:
    try:
        db_cloud.init_tablas()
        st.session_state["db_initialized"] = True
    except Exception:
        pass

st.title("📋 Formato R01-004-21")
st.caption("Terminal Portuario San Nicolás - Inspección a Equipos Electrónicos de Protección")

# --- CABECERA DE LA INSPECCIÓN ---
with st.expander("📌 Datos Generales de la Inspección", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha de Inspección", date.today())
        turno = st.radio("Turno", ["Diurno", "Nocturno"], horizontal=True)
    with col2:
        responsable = st.selectbox("Responsable", ["OPIP", "APP de Guardia", "Supervisor de Protección"])

# --- INVENTARIO OFICIAL DE 43 ÍTEMS POR ZONA ---
INVENTARIO_R01 = [
    # Garita Muelle (1 al 9)
    {"it": 1, "ubi": "Garita Muelle", "eq": "Radio Base", "marca": "ICOM", "serie": "410-283"},
    {"it": 2, "ubi": "Garita Muelle", "eq": "Radio Portátil con cargador", "marca": "MOTOROLA", "serie": "752EYXH436"},
    {"it": 3, "ubi": "Garita Muelle", "eq": "Detector metales", "marca": "HAND-HELD", "serie": "GP 3003B1"},
    {"it": 4, "ubi": "Garita Muelle", "eq": "Teléfono 3431", "marca": "PANASONIC", "serie": "7HCKJ557818"},
    {"it": 5, "ubi": "Garita Muelle", "eq": "PC", "marca": "HP", "serie": "284160"},
    {"it": 6, "ubi": "Garita Muelle", "eq": "Luces de emergencia", "marca": "EXPLORER", "serie": "S/N"},
    {"it": 7, "ubi": "Garita Muelle", "eq": "Otro: Linterna", "marca": "OPALUX", "serie": "OP-8795R"},
    {"it": 8, "ubi": "Garita Muelle", "eq": "Otro: Linterna del bastón de espejo", "marca": "ENERGIZER",
     "serie": "S/N"},
    {"it": 9, "ubi": "Garita Muelle", "eq": "Otro: Estabilizador Radio Base", "marca": "América Suooy",
     "serie": "406-457"},
    # Cabezo (10 al 14)
    {"it": 10, "ubi": "Cabezo", "eq": "Radio Portátil con cargador", "marca": "MOTOROLA", "serie": "752EZ53120"},
    {"it": 11, "ubi": "Cabezo", "eq": "Anexo teléfono 3431", "marca": "PANASONIC", "serie": "KX15105LXW"},
    {"it": 12, "ubi": "Cabezo", "eq": "Altavoz de Muelle", "marca": "GAI –TRONICS", "serie": "S/N"},
    {"it": 13, "ubi": "Cabezo", "eq": "Otro: Linterna", "marca": "ENERGIZER", "serie": "S/N"},
    {"it": 14, "ubi": "Cabezo", "eq": "Otro: Luces de Emergencia", "marca": "ORALUX", "serie": "S/N"},
    # CCTV (15 al 31)
    {"it": 15, "ubi": "CCTV", "eq": "Equipo de monitoreo- DVR", "marca": "PELCO Y HIKVISION", "serie": "S/N"},
    {"it": 16, "ubi": "CCTV", "eq": "Cámara 1 (Ingreso a IP)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 17, "ubi": "CCTV", "eq": "Cámara 2 (Planta Desaladora)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 18, "ubi": "CCTV", "eq": "Cámara 3 (Garita Principal)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 19, "ubi": "CCTV", "eq": "Cámara 4 (Tanques de Petróleo)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 20, "ubi": "CCTV", "eq": "Cámara 5 (Rompe Olas)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 21, "ubi": "CCTV", "eq": "Cámara 6 (Cabezo Muelle)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 22, "ubi": "CCTV", "eq": "Cámara 7 (Garita Muelle Nueva)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 23, "ubi": "CCTV", "eq": "Cámara 8 (Balanza-Control 4)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 24, "ubi": "CCTV", "eq": "Cámara 9 (Plataforma Muelle SS.EE 10)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 25, "ubi": "CCTV", "eq": "Cámara 10 (Bajo Plataforma Muelle)", "marca": "HIKVISION", "serie": "S/N"},
    {"it": 26, "ubi": "CCTV", "eq": "Altavoz de Muelle", "marca": "GAI - TRONICS", "serie": "S/N"},
    {"it": 27, "ubi": "CCTV", "eq": "Radio Portátil", "marca": "MOTOROLA", "serie": "752EYXH546"},
    {"it": 28, "ubi": "CCTV", "eq": "Teléfono 3119", "marca": "PANASONIC", "serie": "1JBKD119348"},
    {"it": 29, "ubi": "CCTV", "eq": "Alarma", "marca": "SM", "serie": "S/N"},
    {"it": 30, "ubi": "CCTV", "eq": "UPS", "marca": "ALLEN BRADLEY", "serie": "S/N"},
    {"it": 31, "ubi": "CCTV", "eq": "Otro: Luces de emergencia", "marca": "EXPLORER", "serie": "388553"},
    # Móvil (32 al 34)
    {"it": 32, "ubi": "Móvil", "eq": "Radio VHF fijo", "marca": "ICOM", "serie": "---"},
    {"it": 33, "ubi": "Móvil", "eq": "Radio Portátil", "marca": "MOTOROLA", "serie": "752EZAD507"},
    {"it": 34, "ubi": "Móvil", "eq": "Linterna / faro", "marca": "SM", "serie": "S/N"},
    # OPIP (35 al 43)
    {"it": 35, "ubi": "OPIP", "eq": "PC (OPIP)", "marca": "HP", "serie": "287-432/ 287-433"},
    {"it": 36, "ubi": "OPIP", "eq": "PC (secretaria)", "marca": "HP", "serie": "287-470/287-471"},
    {"it": 37, "ubi": "OPIP", "eq": "Radio Portátil (canal 14)", "marca": "ICOM IC-M32", "serie": "P6"},
    {"it": 38, "ubi": "OPIP", "eq": "Radio Portátil (canal 14)", "marca": "JVCKENWOOD", "serie": "410-608"},
    {"it": 39, "ubi": "OPIP", "eq": "Radio Portátil (canal 14)", "marca": "JVCKENWOOD", "serie": "410-401"},
    {"it": 40, "ubi": "OPIP", "eq": "Radio Portátil (canal 14)", "marca": "JVCKENWOOD", "serie": "410-403"},
    {"it": 41, "ubi": "OPIP", "eq": "Celular", "marca": "-----------", "serie": "-----------"},
    {"it": 42, "ubi": "OPIP", "eq": "Teléfono 3428 (OPIP)", "marca": "PANASONIC", "serie": "BBKCO67326"},
    {"it": 43, "ubi": "OPIP", "eq": "Teléfono 3510 (Oficina 1)", "marca": "PANASONIC", "serie": "3HBKC094325"}
]


def codificar_imagen_b64(archivo_subido):
    """Convierte un archivo de imagen subido en cadena Base64."""
    if archivo_subido is None:
        return None
    bytes_data = archivo_subido.getvalue()
    return base64.b64encode(bytes_data).decode("utf-8")


zonas = ["Garita Muelle", "Cabezo", "CCTV", "Móvil", "OPIP"]
tabs = st.tabs([f"📍 {z}" for z in zonas])

respuestas = []

for idx, zona in enumerate(zonas):
    with tabs[idx]:
        equipos_zona = [e for e in INVENTARIO_R01 if e["ubi"] == zona]
        for eq in equipos_zona:
            st.markdown(f"**({eq['it']}) {eq['eq']}** — *{eq['marca']} (S/N: {eq['serie']})*")

            col_est, col_chk = st.columns([1.2, 1.8])
            with col_est:
                # 1. Marcado exclusivo OP o INP
                estado = st.radio(
                    "Estado Operativo",
                    options=["OP", "INP"],
                    horizontal=True,
                    key=f"est_{eq['it']}",
                    label_visibility="collapsed"
                )
            with col_chk:
                tiene_obs = st.checkbox(
                    "📝 Añadir Observación / Foto",
                    value=(estado == "INP"),
                    key=f"chk_obs_{eq['it']}"
                )

            obs_item = ""
            foto_1_b64 = None
            foto_2_b64 = None

            if tiene_obs or estado == "INP":
                obs_item = st.text_area(
                    f"Detalle de la observación (Ítem {eq['it']} - {eq['eq']}):",
                    key=f"obs_{eq['it']}",
                    placeholder="Escriba el detalle técnico de la observación...",
                    height=68
                )
                archivos_fotos = st.file_uploader(
                    f"📷 Evidencia fotográfica para Ítem {eq['it']} (Máximo 2 fotos):",
                    type=["jpg", "jpeg", "png"],
                    accept_multiple_files=True,
                    key=f"fotos_{eq['it']}"
                )
                if archivos_fotos:
                    if len(archivos_fotos) > 2:
                        st.warning(
                            "⚠️ Se seleccionaron más de 2 fotos. Solo se incluirán las 2 primeras en el informe.")
                    if len(archivos_fotos) >= 1:
                        foto_1_b64 = codificar_imagen_b64(archivos_fotos[0])
                    if len(archivos_fotos) >= 2:
                        foto_2_b64 = codificar_imagen_b64(archivos_fotos[1])

            respuestas.append({
                "it": eq["it"],
                "ubi": eq["ubi"],
                "eq": eq["eq"],
                "marca": eq["marca"],
                "serie": eq["serie"],
                "estado": estado,
                "obs": obs_item.strip(),
                "foto_1": foto_1_b64,
                "foto_2": foto_2_b64
            })
            st.divider()

obs_gral = st.text_input(
    "Comentario en caso de NO existir ninguna observación en los 43 ítems:",
    "Sin observaciones."
)

# --- GUARDADO Y GENERACIÓN AUTOMÁTICA ---
if st.button("💾 Guardar Inspección y Generar Word Oficial", type="primary", use_container_width=True):
    try:
        with st.spinner("1/2 Sincronizando inspección y evidencias con Turso Cloud..."):
            sql_cab = """
                      INSERT INTO inspecciones_cabecera (codigo_formato, fecha_inspeccion, responsable_inspeccion, \
                                                         turno, observacion_general)
                      VALUES (?, ?, ?, ?, ?); \
                      """
            db_cloud.ejecutar_sql(sql_cab, ["R01-004-21", str(fecha), responsable, turno, obs_gral])

            res_id = db_cloud.ejecutar_sql("SELECT MAX(id) FROM inspecciones_cabecera;")
            cab_id = int(res_id["rows"][0][0]["value"])

            for r in respuestas:
                sql_det = """
                          INSERT INTO inspecciones_detalle
                          (cabecera_id, item_nro, ubicacion, equipo_elemento, marca, serie, estado_operativo, \
                           observacion_item, accion_correctiva, foto_1, foto_2)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); \
                          """
                db_cloud.ejecutar_sql(sql_det, [
                    cab_id,
                    r["it"],
                    r["ubi"],
                    r["eq"],
                    r["marca"],
                    r["serie"],
                    r["estado"],
                    r["obs"],
                    "",
                    r["foto_1"],
                    r["foto_2"]
                ])

        with st.spinner("2/2 Generando documento Word oficial con subíndices y fotografías..."):
            archivo_generado = generador_word.generar_desde_plantilla(inspeccion_id=cab_id)

            st.success(f"✅ ¡Inspección guardada y documento generado! (Folio ID: {cab_id})")
            st.balloons()

            with open(archivo_generado, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Formato Oficial R01-004-21 (.docx)",
                    data=f,
                    file_name=f"R01-004-21_Inspeccion_{cab_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"❌ Error en el proceso: {e}")

# --- DESCARGA HISTÓRICA POR FOLIO ---
st.divider()
with st.expander("🔍 Reimprimir una inspección anterior por Folio ID"):
    folio_antiguo = st.number_input("Ingresa el Folio ID:", min_value=1, value=1, step=1)
    if st.button("📄 Generar Word de este Folio"):
        try:
            doc_antiguo = generador_word.generar_desde_plantilla(inspeccion_id=int(folio_antiguo))
            with open(doc_antiguo, "rb") as f:
                st.download_button(
                    label=f"⬇️ Descargar Folio {folio_antiguo}",
                    data=f,
                    file_name=f"R01-004-21_Inspeccion_{folio_antiguo}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        except Exception as err:
            st.error(f"Error al generar: {err}")