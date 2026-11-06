import toml
import requests

# Carga de credenciales desde secrets.toml o entorno de Streamlit
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

    response = requests.post(ENDPOINT, json=payload, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "error" in data["results"][0]:
        raise RuntimeError(data["results"][0]["error"]["message"])

    return data["results"][0]["response"]["result"]


def init_tablas():
    """Inicializa las tablas y asegura las columnas para hasta 2 fotos por ítem."""
    ejecutar_sql("""
                 CREATE TABLE IF NOT EXISTS inspecciones_cabecera
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     codigo_formato
                     TEXT
                     NOT
                     NULL,
                     fecha_inspeccion
                     TEXT
                     NOT
                     NULL,
                     responsable_inspeccion
                     TEXT
                     NOT
                     NULL,
                     turno
                     TEXT,
                     observacion_general
                     TEXT,
                     fecha_registro
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 );
                 """)
    ejecutar_sql("""
                 CREATE TABLE IF NOT EXISTS inspecciones_detalle
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     cabecera_id
                     INTEGER
                     NOT
                     NULL,
                     item_nro
                     INTEGER
                     NOT
                     NULL,
                     ubicacion
                     TEXT
                     NOT
                     NULL,
                     equipo_elemento
                     TEXT
                     NOT
                     NULL,
                     marca
                     TEXT,
                     serie
                     TEXT,
                     estado_operativo
                     TEXT
                     CHECK (
                     estado_operativo
                     IN
                 (
                     'OP',
                     'INP'
                 )),
                     observacion_item TEXT,
                     accion_correctiva TEXT,
                     foto_1 TEXT,
                     foto_2 TEXT,
                     FOREIGN KEY
                 (
                     cabecera_id
                 ) REFERENCES inspecciones_cabecera
                 (
                     id
                 )
                     );
                 """)

    # Migración defensiva si la tabla ya existía sin columnas de fotos
    res_cols = ejecutar_sql("PRAGMA table_info(inspecciones_detalle);")
    columnas_actuales = [r[1]["value"] for r in res_cols.get("rows", [])]

    if "foto_1" not in columnas_actuales:
        ejecutar_sql("ALTER TABLE inspecciones_detalle ADD COLUMN foto_1 TEXT;")
    if "foto_2" not in columnas_actuales:
        ejecutar_sql("ALTER TABLE inspecciones_detalle ADD COLUMN foto_2 TEXT;")


if __name__ == "__main__":
    init_tablas()
    print("✅ Tablas y columnas de evidencia fotográfica sincronizadas en Turso.")