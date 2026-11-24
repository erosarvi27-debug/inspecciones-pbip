import toml
import requests

# Carga de credenciales desde Streamlit Cloud Secrets o archivo local
try:
    import streamlit as st
    db_url = st.secrets["TURSO_URL"].strip()
    token = st.secrets["TURSO_TOKEN"].strip()
except Exception:
    config = toml.load(".streamlit/secrets.toml")
    db_url = config["TURSO_URL"].strip()
    token = config["TURSO_TOKEN"].strip()

if db_url.startswith("libsql://"):
    db_url = db_url.replace("libsql://", "https://")

ENDPOINT = f"{db_url}/v2/pipeline"
HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def ejecutar_sql(sql: str, params: list = None):
    """Ejecuta una sentencia SQL en Turso vía API HTTPS."""
    stmt = {"sql": sql}
    if params:
        args = []
        for p in params:
            if isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            elif p is None:
                args.append({"type": "null"})
            else:
                args.append({"type": "text", "value": str(p)})
        stmt["args"] = args

    payload = {
        "requests": [
            {"type": "execute", "stmt": stmt},
            {"type": "close"}
        ]
    }

    response = requests.post(ENDPOINT, json=payload, headers=HEADERS, timeout=25)
    response.raise_for_status()
    data = response.json()

    if "error" in data["results"][0]:
        raise RuntimeError(data["results"][0]["error"]["message"])

    return data["results"][0]["response"]["result"]

def init_tablas():
    """Inicializa y migra las tablas para soportar múltiples formatos y hasta 8 fotos (fotos_json)."""
    ejecutar_sql("""
    CREATE TABLE IF NOT EXISTS inspecciones_cabecera (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_formato TEXT NOT NULL,
        fecha_inspeccion TEXT NOT NULL,
        responsable_inspeccion TEXT NOT NULL,
        turno TEXT,
        observacion_general TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    ejecutar_sql("""
    CREATE TABLE IF NOT EXISTS inspecciones_detalle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cabecera_id INTEGER NOT NULL,
        item_nro INTEGER NOT NULL,
        ubicacion TEXT NOT NULL,
        equipo_elemento TEXT NOT NULL,
        marca TEXT,
        serie TEXT,
        estado_operativo TEXT,
        observacion_item TEXT,
        accion_correctiva TEXT,
        foto_1 TEXT,
        foto_2 TEXT,
        fotos_json TEXT,
        FOREIGN KEY (cabecera_id) REFERENCES inspecciones_cabecera(id)
    );
    """)

    # Migración defensiva si aún existiera el CHECK antiguo de solo ('OP', 'INP')
    res_schema = ejecutar_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='inspecciones_detalle';")
    if res_schema.get("rows"):
        create_sql = str(res_schema["rows"][0][0]["value"] or "")
        if "CHECK" in create_sql.upper():
            res_cols = ejecutar_sql("PRAGMA table_info(inspecciones_detalle);")
            cols_ant = [r[1]["value"] for r in res_cols.get("rows", [])]
            if "foto_1" not in cols_ant:
                ejecutar_sql("ALTER TABLE inspecciones_detalle ADD COLUMN foto_1 TEXT;")
            if "foto_2" not in cols_ant:
                ejecutar_sql("ALTER TABLE inspecciones_detalle ADD COLUMN foto_2 TEXT;")
            if "fotos_json" not in cols_ant:
                ejecutar_sql("ALTER TABLE inspecciones_detalle ADD COLUMN fotos_json TEXT;")

            ejecutar_sql("""
            CREATE TABLE IF NOT EXISTS inspecciones_detalle_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cabecera_id INTEGER NOT NULL,
                item_nro INTEGER NOT NULL,
                ubicacion TEXT NOT NULL,
                equipo_elemento TEXT NOT NULL,
                marca TEXT,
                serie TEXT,
                estado_operativo TEXT,
                observacion_item TEXT,
                accion_correctiva TEXT,
                foto_1 TEXT,
                foto_2 TEXT,
                fotos_json TEXT,
                FOREIGN KEY (cabecera_id) REFERENCES inspecciones_cabecera(id)
            );
            """)
            ejecutar_sql("""
            INSERT INTO inspecciones_detalle_new
            (id, cabecera_id, item_nro, ubicacion, equipo_elemento, marca, serie, estado_operativo, observacion_item, accion_correctiva, foto_1, foto_2, fotos_json)
            SELECT id, cabecera_id, item_nro, ubicacion, equipo_elemento, marca, serie, estado_operativo, observacion_item, accion_correctiva, foto_1, foto_2, fotos_json
            FROM inspecciones_detalle;
            """)
            ejecutar_sql("DROP TABLE inspecciones_detalle;")
            ejecutar_sql("ALTER TABLE inspecciones_detalle_new RENAME TO inspecciones_detalle;")

    # Asegurar la columna fotos_json en tablas ya existentes
    res_cols_actual = ejecutar_sql("PRAGMA table_info(inspecciones_detalle);")
    columnas_actuales = [r[1]["value"] for r in res_cols_actual.get("rows", [])]
    if "fotos_json" not in columnas_actuales:
        ejecutar_sql("ALTER TABLE inspecciones_detalle ADD COLUMN fotos_json TEXT;")

if __name__ == "__main__":
    init_tablas()
    print("✅ Base de datos Turso sincronizada con soporte para hasta 8 fotografías (fotos_json).")