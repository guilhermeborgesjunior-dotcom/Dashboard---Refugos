import io
import pandas as pd
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Dashboard de Carga - Horas CT", page_icon="📊", layout="wide"
)

st.title("📊 Dashboard de Carga e Horas Restantes")
st.markdown(
    "Visualização analítica e exportação de dados do arquivo de produção."
)
st.markdown("---")

# Carregamento do arquivo Excel
@st.cache_data
def carregar_dados():
    excel_file = "EXPORT_20260828_095721.XLSX"
    df = pd.read_excel(excel_file, sheet_name="Sheet1")
    return df


try:
    df = carregar_dados()
except Exception as e:
    st.error(
        f"Erro ao carregar o arquivo Excel. Certifique-se de que o arquivo 'EXPORT_20260828_095721.XLSX' está na pasta. Detalhes: {e}"
    )
    st.stop()

# Filtros na Barra Lateral
st.sidebar.header("🔍 Filtros Dinâmicos")

# Filtro de Planejador
planejadores = ["Todos"] + sorted(
    df["Planejador"].dropna().astype(str).unique().tolist()
)
planejador_selecionado = st.sidebar.selectbox(
    "Filtrar por Planejador", planejadores
)

# Filtro de Depósito
depositos = ["Todos"] + sorted(
    df["Descrição do depósito"].dropna().astype(str).unique().tolist()
)
deposito_selecionado = st.sidebar.selectbox("Filtrar por Depósito", depositos)

# Aplicando os filtros
df_filtrado = df.copy()
if planejador_selecionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Planejador"].astype(str) == planejador_selecionado
    ]
if deposito_selecionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Descrição do depósito"].astype(str) == deposito_selecionado
    ]

# KPIs Principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Ordens", len(df_filtrado))
with col2:
    st.metric(
        "Quantidade de Itens (Ordem)",
        f"{df_filtrado['Qtde Ordem'].sum():,.0f}",
    )
with col3:
    st.metric(
        "Carga Horária Restante",
        f"{df_filtrado['Tempo Restante da Operação'].sum():,.2f} h",
    )
with col4:
    st.metric(
        "Média Horas/Operação",
        f"{df_filtrado['Tempo Restante da Operação'].mean():,.2f} h",
    )

st.markdown("---")

# Seção de Gráficos e Tabela
st.subheader("📋 Dados Detalhados e Filtrados")
st.dataframe(df_filtrado, use_container_width=True)

# Botão de Exportação para Excel
st.markdown("### 📥 Exportar Dados Filtrados")


def converter_para_excel(df_export):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Dados_Filtrados")
    processed_data = output.getvalue()
    return processed_data


excel_data = converter_para_excel(df_filtrado)

st.download_button(
    label="📥 Baixar Dados Filtrados em Excel (.xlsx)",
    data=excel_data,
    file_name="dados_filtrados_dashboard.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
