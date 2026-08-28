import pandas as pd
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Dashboard Horas CT", page_icon="📊", layout="wide"
)

st.title("📊 Dashboard Horas CT - Controle de Carga Pendente")
st.markdown("---")

# Dados simulados (substitua futuramente por leitura de base ou SQLite)
data = {
    "Centro de Trabalho": ["CT-01", "CT-02", "CT-01", "CT-03"],
    "Peça": [
        "Eixo Principal",
        "Carcaça Superior",
        "Engrenagem",
        "Tampa Inferior",
    ],
    "Horas Pendentes": [24.5, 12.0, 18.3, 8.0],
    "Status APQ": ["Pendente", "Liberado", "Em Andamento", "Liberado"],
    "Observação": [
        "Aguardando material",
        "Usinagem em curso",
        "Revisão de processo",
        "Liberado para montagem",
    ],
}

df = pd.DataFrame(data)

# Métricas globais (KPIs)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="Total de Horas Pendentes",
        value=f"{df['Horas Pendentes'].sum():.1f}h",
    )
with col2:
    st.metric(
        label="Centros de Trabalho", value=df["Centro de Trabalho"].nunique()
    )
with col3:
    st.metric(
        label="Itens Liberados (APQ)",
        value=len(df[df["Status APQ"] == "Liberado"]),
    )

st.markdown("---")

# Filtro lateral e busca
st.sidebar.header("Filtros")
ct_filtro = st.sidebar.selectbox(
    "Filtrar Centro de Trabalho", ["Todos"] + list(df["Centro de Trabalho"].unique())
)

df_filtrado = (
    df if ct_filtro == "Todos" else df[df["Centro de Trabalho"] == ct_filtro]
)

# Tabela Interativa
st.subheader("Registros Operacionais")
st.dataframe(df_filtrado, use_container_width=True)
