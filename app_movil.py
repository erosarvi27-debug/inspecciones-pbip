import base64
import streamlit as st
from datetime import date
import db_cloud
import generador_word

st.set_page_config(
    page_title="SGCS PBIP - Terminal Portuario San Nicolás",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO EJECUTIVO CORPORATIVO (CSS) ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
        color: white;
        padding: 1.4rem 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
        border-left: 6px solid #e63946;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .main-header h2 {
        margin: 0;
        font-size: 1.45rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.3px;
    }
    .main-header p {
        margin: 0.25rem 0 0 0;
        font-size: 0.92rem;
        color: #dce4f0;
    }
    .item-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #134074;
        border-radius: 8px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .item-title {
        font-size: 0.98rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .item-sub {
        font-size: 0.82rem;
        color: #64748b;
    }
    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        text-align: center;
    }
    .metric-val {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0b2545;
    }
    .metric-lbl {
        font-size: 0.78rem;
        color: #475569;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización automática de la base de datos en Turso
if "db_initialized_v2" not in st.session_state:
    try:
        db_cloud.init_tablas()
        st.session_state["db_initialized_v2"] = True
    except Exception:
        pass

# ==============================================================================
# CATÁLOGO OFICIAL DE LOS 5 FORMATOS DE INSPECCIÓN PBIP
# ==============================================================================
CATALOGO_FORMATOS = {
    "R01-004-21": {
        "titulo": "R01-004-21 | Inspección de Equipos Electrónicos de Protección",
        "subtitulo": "Verificación de operatividad de radios, CCTV, teléfonos, alarmas y luces de emergencia",
        "tipo": "EQUIPOS",
        "opciones": ["OP", "INP"]
    },
    "R03-004-21": {
        "titulo": "R03-004-21 | Lista de Verificación de Barreras Perimetrales y Accesos",
        "subtitulo": "Inspección física de muros, cercos, control de pases, visitas y estacionamientos (32 puntos)",
        "tipo": "CHECKLIST",
        "opciones": ["SI", "NO", "N/A", "P/A"]
    },
    "R06-004-21": {
        "titulo": "R06-004-21 | Control e Inspección de Iluminación del Terminal",
        "subtitulo": "Verificación de luminarias perimetrales, áreas operativas, muelle, escaleras y luces de emergencia",
        "tipo": "CHECKLIST",
        "opciones": ["SI", "NO", "N/A", "P/A"]
    },
    "R07-004-21": {
        "titulo": "R07-004-21 | Inspección de Puertas de Acceso al Terminal",
        "subtitulo": "Verificación de estructura, supervisión, tableros de llaves, CCTV y registros de acceso",
        "tipo": "CHECKLIST",
        "opciones": ["SI", "NO", "N/A", "P/A"]
    },
    "R08-004-21": {
        "titulo": "R08-004-21 | Inspección de Dispositivos de Cierre, Candados y Llaves",
        "subtitulo": "Control de candados, chapas, puertas peatonales/vehiculares, S.E.E., Gantry y tablero de llaves",
        "tipo": "CHECKLIST",
        "opciones": ["SI", "NO", "N/A", "P/A"]
    }
}

INVENTARIO_R01 = [
    {"it": 1, "ubi": "Garita Muelle", "eq": "Radio Base", "marca": "ICOM", "serie": "410-283"},
    {"it": 2, "ubi": "Garita Muelle", "eq": "Radio Portátil con cargador", "marca": "MOTOROLA", "serie": "752EYXH436"},
    {"it": 3, "ubi": "Garita Muelle", "eq": "Detector metales", "marca": "HAND-HELD", "serie": "GP 3003B1"},
    {"it": 4, "ubi": "Garita Muelle", "eq": "Teléfono 3431", "marca": "PANASONIC", "serie": "7HCKJ557818"},
    {"it": 5, "ubi": "Garita Muelle", "eq": "PC", "marca": "HP", "serie": "284160"},
    {"it": 6, "ubi": "Garita Muelle", "eq": "Luces de emergencia", "marca": "EXPLORER", "serie": "S/N"},
    {"it": 7, "ubi": "Garita Muelle", "eq": "Otro: Linterna", "marca": "OPALUX", "serie": "OP-8795R"},
    {"it": 8, "ubi": "Garita Muelle", "eq": "Otro: Linterna del bastón de espejo", "marca": "ENERGIZER", "serie": "S/N"},
    {"it": 9, "ubi": "Garita Muelle", "eq": "Otro: Estabilizador Radio Base", "marca": "América Suooy", "serie": "406-457"},
    {"it": 10, "ubi": "Cabezo", "eq": "Radio Portátil con cargador", "marca": "MOTOROLA", "serie": "752EZ53120"},
    {"it": 11, "ubi": "Cabezo", "eq": "Anexo teléfono 3431", "marca": "PANASONIC", "serie": "KX15105LXW"},
    {"it": 12, "ubi": "Cabezo", "eq": "Altavoz de Muelle", "marca": "GAI –TRONICS", "serie": "S/N"},
    {"it": 13, "ubi": "Cabezo", "eq": "Otro: Linterna", "marca": "ENERGIZER", "serie": "S/N"},
    {"it": 14, "ubi": "Cabezo", "eq": "Otro: Luces de Emergencia", "marca": "ORALUX", "serie": "S/N"},
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
    {"it": 32, "ubi": "Móvil", "eq": "Radio VHF fijo", "marca": "ICOM", "serie": "---"},
    {"it": 33, "ubi": "Móvil", "eq": "Radio Portátil", "marca": "MOTOROLA", "serie": "752EZAD507"},
    {"it": 34, "ubi": "Móvil", "eq": "Linterna / faro", "marca": "SM", "serie": "S/N"},
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

PREGUNTAS_CHECKLIST = {
    "R03-004-21": [
        # Hoja 1 (1 al 17)
        {"it": 1, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Existe un muro, reja o cerco perimetral adecuado y conforme a los estándares reconocidos de la industria?"},
        {"it": 2, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿El muro, reja o cerco perimetral está intacto?"},
        {"it": 3, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Se inspecciona las murallas de albañilería o ladrillo cada 3 meses para determinar su efectividad y estimar cualquier reparación necesaria debido a erosión y uso?"},
        {"it": 4, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "Si hay murallas de edificios, pisos o techos que formen parte de la barrera ¿Se complementan con otros medios de detección de intrusos, como CCTV o sensores de detección de movimiento?"},
        {"it": 5, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿El área adyacente a las barreras perimétricas están libre de escombros o basura?"},
        {"it": 6, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Son las barreras u otras entradas en las barreras perimetrales, mantenidas en un número mínimo para seguridad y eficiencia de la operación?"},
        {"it": 7, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Las barreras de acceso proveen una protección equivalente a la de la barrera de la cual forman parte?"},
        {"it": 8, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Las puertas de ingreso del exterior están aseguradas?"},
        {"it": 9, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿El encargado del área tiene las llaves de estas puertas?"},
        {"it": 10, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Se usa un sistema de identificación de pase o placa para identificar a todo el personal?"},
        {"it": 11, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿El muro o cercado posee coronamiento de alambre de púas u otro obstáculo?"},
        {"it": 12, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Posee red de luz perimetral?"},
        {"it": 13, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Existen garitas de control?"},
        {"it": 14, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Se requiere de todo el personal que porte una tarjeta de identificación con foto, a la vista, todo el tiempo que trabaje dentro de la instalación?"},
        {"it": 15, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "¿Provee el sistema de identificación en uso, el grado adecuado de seguridad?"},
        {"it": 16, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "El personal al que no se le ha entregado una tarjeta de identificación permanente ¿Es tratado como visita y se le entrega una tarjeta de visita?"},
        {"it": 17, "ubi": "Hoja 1 - Barreras y Accesos", "eq": "En los puntos de acceso, ¿Los guardias comparan los pases con los portadores al ingreso?"},
        # Hoja 2 (18 al 32)
        {"it": 18, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Es adecuada la supervisión de la identificación del personal y del sistema de control?"},
        {"it": 19, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se registran y controlan los pases y números de serie por procedimientos estrictos de contabilidad?"},
        {"it": 20, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se reemplazan las tarjetas de identificación perdidas con TI con diferente número de serie?"},
        {"it": 21, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se ha establecido un procedimiento para la entrega de pases temporales para los individuos que olvidaron su pase permanente?"},
        {"it": 22, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Son los pases de un diseño y apariencia tales que permitan a los guardias y otro personal reconocer rápida y positivamente las autorizaciones y limitaciones aplicables al portador?"},
        {"it": 23, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Existe un procedimiento para exigir la devolución del pase de identificación al término del empleo o asignación?"},
        {"it": 24, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Les está prohibido a los choferes de camiones, vendedores y otros visitantes el ingreso a las oficinas, excepto para lo requerido por el negocio, y solamente el personal autorizado está permitido en las bodegas?"},
        {"it": 25, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se mantiene y está fácilmente accesible un registro permanente de visitas?"},
        {"it": 26, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se efectúan inspecciones administrativas aleatorias a los vehículos que ingresan a las instalaciones?"},
        {"it": 27, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Es el acceso a las áreas de estacionamiento supervisado y restringido por un sistema de permiso para los vehículos particulares y de contratistas?"},
        {"it": 28, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se mantiene registros de permisos de estacionamiento que incluyan parear al personal con el número de permiso y de placa patente?"},
        {"it": 29, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Se exige a todos los vehículos estacionar en las áreas designadas?"},
        {"it": 30, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Está el estacionamiento para empleados, estibadores y visitantes, alejado al menos 20 metros de los muelles y dársenas y fuera de las áreas operacionales, de manejo de carga y de almacenamiento?"},
        {"it": 31, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Están todos los permisos temporales de estacionamiento entregados a vendedores y visitantes, circunscritos a determinada área?"},
        {"it": 32, "ubi": "Hoja 2 - Pases y Estacionamiento", "eq": "¿Están aseguradas apropiadamente todas las aberturas tales como las cámaras de alcantarillado y de servicios y cualquier otra que permita acceso a la Instalación?"}
    ],
    "R06-004-21": [
        {"it": 1, "ubi": "Iluminación General", "eq": "¿La iluminación perimetral es adecuada?"},
        {"it": 2, "ubi": "Iluminación General", "eq": "¿La iluminación del Área Operativa del Terminal es adecuada?"},
        {"it": 3, "ubi": "Iluminación General", "eq": "¿Las áreas de talleres se encuentran iluminadas?"},
        {"it": 4, "ubi": "Iluminación General", "eq": "¿Las áreas de almacenaje están bien iluminadas?"},
        {"it": 5, "ubi": "Iluminación General", "eq": "¿Las áreas de embarque y recepción de carga están debidamente iluminadas?"},
        {"it": 6, "ubi": "Iluminación General", "eq": "¿Las puertas principales de acceso, zonas de carga y áreas restringidas están correctamente iluminadas?"},
        {"it": 7, "ubi": "Iluminación General", "eq": "¿Los parqueaderos se encuentran correctamente iluminados?"},
        {"it": 8, "ubi": "Iluminación General", "eq": "¿Las áreas restringidas poseen sistema de iluminación de emergencia?"},
        {"it": 9, "ubi": "Iluminación General", "eq": "¿Se mantienen limpios los postes y luminarias del Terminal?"},
        {"it": 10, "ubi": "Iluminación General", "eq": "¿Los interruptores se encuentran en buen estado?"},
        {"it": 11, "ubi": "Iluminación General", "eq": "¿Las luminarias de la parte inferior del muelle están operativas?"},
        {"it": 12, "ubi": "Iluminación General", "eq": "¿La iluminación de la parte inferior del muelle es apropiada?"},
        {"it": 13, "ubi": "Iluminación General", "eq": "¿Se cuenta con reflectores o faros piratas?"},
        {"it": 14, "ubi": "Iluminación Escaleras y Emergencia", "eq": "a.- Gantry (¿Las escalas o escaleras se encuentran iluminadas?)"},
        {"it": 15, "ubi": "Iluminación Escaleras y Emergencia", "eq": "b.- Muelle (¿Las escalas o escaleras se encuentran iluminadas?)"},
        {"it": 16, "ubi": "Iluminación Escaleras y Emergencia", "eq": "c.- Cabezo (¿Las escalas o escaleras se encuentran iluminadas?)"},
        {"it": 17, "ubi": "Iluminación Escaleras y Emergencia", "eq": "¿Existen luces de emergencia?"},
        {"it": 18, "ubi": "Iluminación Escaleras y Emergencia", "eq": "¿Se cumple el programa de mantenimiento?"}
    ],
    "R07-004-21": [
        {"it": 1, "ubi": "Puertas de Acceso", "eq": "¿Las puertas de acceso al terminal son adecuadas en cuanto a su estructura?"},
        {"it": 2, "ubi": "Puertas de Acceso", "eq": "¿Las puertas de acceso al Terminal son controladas por personal de seguridad?"},
        {"it": 3, "ubi": "Puertas de Acceso", "eq": "¿Los operadores de las puertas son supervisados?"},
        {"it": 4, "ubi": "Puertas de Acceso", "eq": "¿Las puertas tienen candados o chapas que dificultan un fácil acceso a personal no autorizado?"},
        {"it": 5, "ubi": "Puertas de Acceso", "eq": "¿El encargado del área mantiene las llaves de las puertas?"},
        {"it": 6, "ubi": "Puertas de Acceso", "eq": "¿El tablero de llaves permanece cerrado y en lugar seguro?"},
        {"it": 7, "ubi": "Puertas de Acceso", "eq": "¿La llave que abre el tablero de llaves se conserva en sobre lacrado?"},
        {"it": 8, "ubi": "Puertas de Acceso", "eq": "¿El área adyacente a las puertas está libre de obstáculos como escombros y basura?"},
        {"it": 9, "ubi": "Puertas de Acceso", "eq": "¿Se cuenta con algún sistema de registro que incluya fotografía para personas y vehículos?"},
        {"it": 10, "ubi": "Puertas de Acceso", "eq": "¿Las puertas están monitoreadas por CCTV y se cuenta con central de monitoreo y grabación de este sistema?"},
        {"it": 11, "ubi": "Puertas de Acceso", "eq": "¿Se cuenta con un sistema que registra la hora de ingreso y salida de las personas y vehículos que usan las puertas?"},
        {"it": 12, "ubi": "Puertas de Acceso", "eq": "¿El número de puertas de la instalación es el mínimo necesario que requiere la instalación para el acceso de personas y carga?"},
        {"it": 13, "ubi": "Puertas de Acceso", "eq": "¿Las puertas al estar cerradas proporcionan tanta seguridad como las barreras perimétricas de la cual forman parte?"}
    ],
    "R08-004-21": [
        {"it": 1, "ubi": "Candados y Control de Llaves", "eq": "¿Las puertas y ventanas que dan al exterior cuentan con dispositivos y candados para su protección?"},
        {"it": 2, "ubi": "Candados y Control de Llaves", "eq": "¿Las llaves son debidamente guardadas y controladas?"},
        {"it": 3, "ubi": "Candados y Control de Llaves", "eq": "¿Se les da un mantenimiento apropiado a los dispositivos de cierre y seguros?"},
        {"it": 4, "ubi": "Candados y Control de Llaves", "eq": "¿Los candados son cambiados regularmente?"},
        {"it": 5, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de acceso peatonal está en buen estado?"},
        {"it": 6, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de acceso vehicular está en buen estado?"},
        {"it": 7, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de acceso a la garita de control está en buen estado?"},
        {"it": 8, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de acceso al CCTV está en buen estado?"},
        {"it": 9, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de acceso a las S.E.E. están en buen estado?"},
        {"it": 10, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de acceso a la caseta de control del gantry está en buen estado?"},
        {"it": 11, "ubi": "Candados y Control de Llaves", "eq": "¿El candado, chapa o seguro de la puerta de la garita del cabezo está en buen estado?"},
        {"it": 12, "ubi": "Candados y Control de Llaves", "eq": "¿Todas las otras áreas que deben poseer dispositivos de cierre y candados cuentan con estos mecanismos de seguridad?"},
        {"it": 13, "ubi": "Candados y Control de Llaves", "eq": "¿Las llaves están separadas de acuerdo a la sensibilidad en diferentes dispositivos de almacenamiento?"},
        {"it": 14, "ubi": "Candados y Control de Llaves", "eq": "¿Las llaves son guardadas en un lugar establecido al finalizar la jornada de trabajo?"},
        {"it": 15, "ubi": "Candados y Control de Llaves", "eq": "¿Existe procedimiento de control de llaves?"},
        {"it": 16, "ubi": "Candados y Control de Llaves", "eq": "¿Está implementado tablero de control de llaves?"},
        {"it": 17, "ubi": "Candados y Control de Llaves", "eq": "¿El Agente domina el procedimiento a seguir para el empleo del tablero de control de llaves?"}
    ]
}

def codificar_imagen_b64(archivo_subido):
    if archivo_subido is None:
        return None
    return base64.b64encode(archivo_subido.getvalue()).decode("utf-8")

# ==============================================================================
# BARRA LATERAL EJECUTIVA (SELECTOR DE FORMATO Y ARCHIVO HISTÓRICO)
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚓ **SHP - TP SAN NICOLÁS**")
    st.caption("Sistema de Gestión en Control y Seguridad (PBIP / BASC)")
    st.divider()

    formato_sel = st.selectbox(
        "📂 Seleccione Formato Oficial:",
        options=list(CATALOGO_FORMATOS.keys()),
        format_func=lambda k: CATALOGO_FORMATOS[k]["titulo"]
    )

    st.divider()
    st.markdown("#### 📌 Datos de Cabecera")
    fecha = st.date_input("Fecha de Inspección", date.today())
    turno = st.radio("Turno Operativo", ["Diurno", "Nocturno"], horizontal=True)
    responsable = st.selectbox("Responsable de Inspección", ["OPIP", "Supervisor de Protección", "APP de Guardia"])

    st.divider()
    st.markdown("#### 🔍 Historial / Reimpresión")
    folio_antiguo = st.number_input("Folio ID a consultar:", min_value=1, value=1, step=1)
    if st.button("📄 Descargar Folio Histórico", use_container_width=True):
        try:
            doc_ant = generador_word.generar_desde_plantilla(inspeccion_id=int(folio_antiguo))
            with open(doc_ant, "rb") as f:
                st.download_button(
                    label=f"⬇️ Guardar Word (Folio {folio_antiguo})",
                    data=f,
                    file_name=doc_ant,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        except Exception as err:
            st.error(f"Error: {err}")

# ==============================================================================
# CUERPO PRINCIPAL EJECUTIVO
# ==============================================================================
info_fmt = CATALOGO_FORMATOS[formato_sel]

st.markdown(f"""
<div class="main-header">
    <h2>🛡️ {info_fmt['titulo']}</h2>
    <p>{info_fmt['subtitulo']} — <b>Shougang Hierro Perú S.A.A.</b></p>
</div>
""", unsafe_allow_html=True)

items_actuales = INVENTARIO_R01 if formato_sel == "R01-004-21" else PREGUNTAS_CHECKLIST[formato_sel]
opciones_estado = info_fmt["opciones"]
estado_defecto_alerta = "INP" if formato_sel == "R01-004-21" else "NO"

# Agrupar por pestañas según la ubicación o sección
zonas = []
for item in items_actuales:
    if item["ubi"] not in zonas:
        zonas.append(item["ubi"])

tabs = st.tabs([f"📍 {z}" for z in zonas])
respuestas = []

for idx, zona in enumerate(zonas):
    with tabs[idx]:
        items_zona = [e for e in items_actuales if e["ubi"] == zona]
        for eq in items_zona:
            key_prefix = f"{formato_sel}_{eq['it']}"
            sub_info = f"Marca: {eq.get('marca', '-')} | Serie: {eq.get('serie', '-')}" if formato_sel == "R01-004-21" else f"Requisito de Verificación #{eq['it']}"

            st.markdown(f"""
            <div class="item-card">
                <div class="item-title">({eq['it']}) {eq['eq']}</div>
                <div class="item-sub">{sub_info}</div>
            </div>
            """, unsafe_allow_html=True)

            col_est, col_chk = st.columns([1.6, 1.4])
            with col_est:
                estado = st.radio(
                    f"Estado {eq['it']}",
                    options=opciones_estado,
                    horizontal=True,
                    key=f"est_{key_prefix}",
                    label_visibility="collapsed"
                )
            with col_chk:
                tiene_obs = st.checkbox(
                    "📝 Registrar Observación / Evidencia Fotográfica",
                    value=(estado == estado_defecto_alerta),
                    key=f"chk_{key_prefix}"
                )

            obs_item = ""
            foto_1_b64 = None
            foto_2_b64 = None

            if tiene_obs or (estado == estado_defecto_alerta):
                c_obs, c_fot = st.columns([1.3, 1.2])
                with c_obs:
                    obs_item = st.text_area(
                        f"Detalle técnico del hallazgo (Ítem {eq['it']}):",
                        key=f"obs_{key_prefix}",
                        placeholder="Describa la observación o condición detectada...",
                        height=85
                    )
                with c_fot:
                    archivos_fotos = st.file_uploader(
                        f"📷 Evidencia fotográfica (Máx. 2 fotos - 4.16x7.00 cm):",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        key=f"fot_{key_prefix}"
                    )
                    if archivos_fotos:
                        if len(archivos_fotos) > 2:
                            st.warning("⚠️ Solo se incluirán las 2 primeras fotografías.")
                        if len(archivos_fotos) >= 1:
                            foto_1_b64 = codificar_imagen_b64(archivos_fotos[0])
                        if len(archivos_fotos) >= 2:
                            foto_2_b64 = codificar_imagen_b64(archivos_fotos[1])

            respuestas.append({
                "it": eq["it"],
                "ubi": eq["ubi"],
                "eq": eq["eq"],
                "marca": eq.get("marca", ""),
                "serie": eq.get("serie", ""),
                "estado": estado,
                "obs": obs_item.strip(),
                "foto_1": foto_1_b64,
                "foto_2": foto_2_b64
            })

# --- RESUMEN EJECUTIVO EN TIEMPO REAL ---
st.divider()
total_it = len(respuestas)
total_obs = sum(1 for r in respuestas if r["obs"] or r["foto_1"] or r["foto_2"])
total_ok = sum(1 for r in respuestas if r["estado"] in ["OP", "SI"])

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-box"><div class="metric-val">{formato_sel}</div><div class="metric-lbl">Formato Activo</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="metric-val">{total_it}</div><div class="metric-lbl">Total Ítems Evaluados</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#16a34a;">{total_ok}</div><div class="metric-lbl">Operativos / Cumple</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#dc2626;">{total_obs}</div><div class="metric-lbl">Observaciones (OBS)</div></div>', unsafe_allow_html=True)

st.write("")
obs_gral = st.text_input(
    "Comentario General (Se imprimirá en caso de no existir observaciones específicas):",
    "Sin observaciones."
)

if st.button("💾 GUARDAR INSPECCIÓN EN LA NUBE Y GENERAR WORD OFICIAL", type="primary", use_container_width=True):
    try:
        with st.spinner("1/2 Sincronizando registro y fotografías en Turso Cloud..."):
            sql_cab = """
            INSERT INTO inspecciones_cabecera (codigo_formato, fecha_inspeccion, responsable_inspeccion, turno, observacion_general)
            VALUES (?, ?, ?, ?, ?);
            """
            db_cloud.ejecutar_sql(sql_cab, [formato_sel, str(fecha), responsable, turno, obs_gral])

            res_id = db_cloud.ejecutar_sql("SELECT MAX(id) FROM inspecciones_cabecera;")
            cab_id = int(res_id["rows"][0][0]["value"])

            for r in respuestas:
                sql_det = """
                INSERT INTO inspecciones_detalle 
                (cabecera_id, item_nro, ubicacion, equipo_elemento, marca, serie, estado_operativo, observacion_item, accion_correctiva, foto_1, foto_2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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

        with st.spinner("2/2 Compilando plantilla Word oficial con subíndices y evidencias..."):
            archivo_generado = generador_word.generar_desde_plantilla(inspeccion_id=cab_id)
            st.success(f"✅ ¡Inspección {formato_sel} registrada correctamente! (Folio N° {cab_id})")

            with open(archivo_generado, "rb") as f:
                st.download_button(
                    label=f"⬇️ DESCARGAR DOCUMENTO OFICIAL {formato_sel} (FOLIO {cab_id})",
                    data=f,
                    file_name=archivo_generado,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"❌ Error al procesar la inspección: {e}")