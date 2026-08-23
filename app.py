import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Dashboard Refugos - UFE", layout="wide")

st.title("⚠️ Dashboard Refugos - UFE")
st.caption("Monitoramento de perdas operacionais e análise de causa raiz")

# Importação de arquivo (Excel ou CSV)
uploaded_file = st.sidebar.file_uploader("Importar arquivo (Excel ou CSV)", type=["xlsx", "xls", "xlsm", "csv"])

if uploaded_file is not None:
    # Leitura do arquivo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Padronização de colunas
    df.columns = [c.strip().lower() for c in df.columns]

    # Cálculos de KPIs
    total_produzido = df['qtdproduzida'].sum() if 'qtdproduzida' in df.columns else 0
    total_refugado = df['qtdrefugada'].sum() if 'qtdrefugada' in df.columns else 0
    
    if 'custounitario' in df.columns and 'qtdrefugada' in df.columns:
        custo_total = (df['qtdrefugada'] * df['custounitario']).sum()
    else:
        custo_total = 0
        
    taxa_refugo = (total_refugado / total_produzido * 100) if total_produzido > 0 else 0

    # Exibição dos KPIs em Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Refugado", f"{total_refugado:,.0f} pçs".replace(",", "."))
    col2.metric("Taxa de Refugo Geral", f"{taxa_refugo:.2f}%", delta_color="inverse")
    col3.metric("Custo Total", f"R$ {custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col4.metric("Total Produzido", f"{total_produzido:,.0f} pçs".replace(",", "."))

    st.divider()

    # Gráficos
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Pareto: Motivos de Refugo")
        if 'motivo' in df.columns and 'qtdrefugada' in df.columns:
            pareto_df = df.groupby('motivo')['qtdrefugada'].sum().reset_index().sort_values(by='qtdrefugada', ascending=False)
            st.bar_chart(pareto_df.set_index('motivo'))

    with c2:
        st.subheader("Evolução Temporal")
        if 'data' in df.columns and 'qtdrefugada' in df.columns:
            trend_df = df.groupby('data')['qtdrefugada'].sum().reset_index()
            st.line_chart(trend_df.set_index('data'))

    st.divider()

    # Tabela detalhada
    st.subheader("Detalhamento dos Dados")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Por favor, faça o upload de um arquivo do Excel (.xlsx) ou CSV no menu lateral para visualizar os indicadores.")
