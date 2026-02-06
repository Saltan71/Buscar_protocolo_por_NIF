import streamlit as st
import pandas as pd
from io import BytesIO

# ---------------- CONFIGURACIÓN ----------------
st.set_page_config(layout="wide")
st.title("Buscar protocolos por NIF")

COL_NIF = "NIF"

# Campos a conservar (ajusta si lo necesitas)
CAMPOS_TABLA_1 = ["NIF", "NOMBRE", "EXPEDIENTE"]
CAMPOS_TABLA_2 = ["NIF", "PROTOCOLO", "FECHA"]

CHUNK_SIZE = 200_000

# ---------------- FUNCIONES ----------------
def leer_archivo(file, chunksize=None):
    """Lee CSV (con separador automático) o Excel"""
    if file.name.lower().endswith(".xlsx"):
        return pd.read_excel(file, dtype=str)
    else:
        return pd.read_csv(
            file,
            sep=None,
            engine="python",
            dtype=str,
            chunksize=chunksize
        )

def to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return buffer.getvalue()

# ---------------- SUBIDA DE ARCHIVOS ----------------
f1 = st.file_uploader(
    "Archivo 1 · NIF buscados",
    type=["csv", "xlsx"]
)

f2 = st.file_uploader(
    "Archivo 2 · Archivo grande",
    type=["csv", "xlsx"]
)

# ---------------- LÓGICA PRINCIPAL ----------------
if f1 and f2:
    # ---- ARCHIVO 1 ----
    df1 = leer_archivo(f1)
    df1 = df1[CAMPOS_TABLA_1]
    nifs_buscados = set(df1[COL_NIF].dropna())

    st.info(f"NIFs a buscar: {len(nifs_buscados)}")

    # ---- ARCHIVO 2 ----
    resultados = []
    progress = st.progress(0)

    if f2.name.lower().endswith(".xlsx"):
        df2 = leer_archivo(f2)
        df2_filtrado = df2[df2[COL_NIF].isin(nifs_buscados)]
        resultados.append(df2_filtrado[CAMPOS_TABLA_2])
        progress.progress(1.0)

    else:
        for i, chunk in enumerate(leer_archivo(f2, chunksize=CHUNK_SIZE)):
            chunk_filtrado = chunk[chunk[COL_NIF].isin(nifs_buscados)]
            if not chunk_filtrado.empty:
                resultados.append(chunk_filtrado[CAMPOS_TABLA_2])
            progress.progress(min((i + 1) / 50, 1.0))

    # ---- RESULTADO ----
    if resultados:
        df2_filtrado = pd.concat(resultados, ignore_index=True)
        df_final = df1.merge(df2_filtrado, on=COL_NIF, how="left")

        st.success(f"Registros resultantes: {len(df_final)}")

        # ---- TABLA EDITABLE (OFICIAL STREAMLIT) ----
        df_editado = st.data_editor(
            df_final,
            use_container_width=True,
            num_rows="dynamic"
        )

        # ---- DESCARGAS ----
        csv = df_editado.to_csv(index=False, sep=";").encode("utf-8")
        excel = to_excel(df_editado)

        col1, col2 = st.columns(2)
        col1.download_button(
            "Descargar CSV",
            csv,
            "resultado_NIF.csv",
            "text/csv"
        )
        col2.download_button(
            "Descargar Excel",
            excel,
            "resultado_NIF.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No se encontraron coincidencias.")
