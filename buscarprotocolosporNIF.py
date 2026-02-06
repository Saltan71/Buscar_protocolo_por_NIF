import streamlit as st
import pandas as pd
from streamlit_handsontable import hot_table
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Buscar protocolos por NIF")

# --- CONFIGURACIÓN ---
COL_NIF = "NIF"

CAMPOS_TABLA_1 = ["NIF", "NOMBRE", "EXPEDIENTE"]
CAMPOS_TABLA_2 = ["NIF", "PROTOCOLO", "FECHA"]

CHUNK_SIZE = 200_000

# --- FUNCIONES ---
def leer_archivo(file, nrows=None, chunksize=None):
    if file.name.endswith(".xlsx"):
        return pd.read_excel(file, dtype=str)
    else:
        return pd.read_csv(
            file,
            sep=None,
            engine="python",
            dtype=str,
            nrows=nrows,
            chunksize=chunksize
        )

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return output.getvalue()

# --- SUBIDA ---
f1 = st.file_uploader("Archivo 1 (NIF buscados)", type=["csv", "xlsx"])
f2 = st.file_uploader("Archivo 2 (archivo grande)", type=["csv", "xlsx"])

if f1 and f2:
    # --- ARCHIVO 1 ---
    df1 = leer_archivo(f1)
    df1 = df1[CAMPOS_TABLA_1]
    nifs = set(df1[COL_NIF].dropna().unique())

    st.info(f"NIFs a buscar: {len(nifs)}")

    # --- ARCHIVO 2 ---
    resultados = []
    progress = st.progress(0)
    total_chunks = 0

    if f2.name.endswith(".xlsx"):
        df2 = leer_archivo(f2)
        df2_filtrado = df2[df2[COL_NIF].isin(nifs)][CAMPOS_TABLA_2]
        resultados.append(df2_filtrado)
        progress.progress(1.0)
    else:
        for i, chunk in enumerate(leer_archivo(f2, chunksize=CHUNK_SIZE)):
            total_chunks += 1
            chunk_filtrado = chunk[chunk[COL_NIF].isin(nifs)]
            if not chunk_filtrado.empty:
                resultados.append(chunk_filtrado[CAMPOS_TABLA_2])
            progress.progress(min((i + 1) / 50, 1.0))  # estimación visual

    if resultados:
        df2_filtrado = pd.concat(resultados, ignore_index=True)
        df_final = df1.merge(df2_filtrado, on=COL_NIF, how="left")

        st.success(f"Registros resultantes: {len(df_final)}")

        # --- TABLA ---
        hot_table(
            df_final,
            height=600,
            license_key="non-commercial-and-evaluation"
        )

        # --- DESCARGAS ---
        csv = df_final.to_csv(index=False, sep=";").encode("utf-8")
        excel = to_excel(df_final)

        col1, col2 = st.columns(2)
        col1.download_button("Descargar CSV", csv, "resultado_NIF.csv", "text/csv")
        col2.download_button(
            "Descargar Excel",
            excel,
            "resultado_NIF.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No hay coincidencias.")
