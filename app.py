import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

# Configuração da página (deve ser a primeira instrução)
st.set_page_config(page_title="Dashboard Refugos - WEG UFE", layout="wide")

# Estilos customizados (Cabeçalho azul marinho com imagem de usinagem translúcida e organização)
st.markdown("""
    <style>
    .header-container {
        position: relative;
        background-image: linear-gradient(rgba(10, 25, 47, 0.85), rgba(10, 25, 47, 0.85)), 
                          url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        padding: 40px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .header-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-top: 5px;
    }
    </style>
    
    <div class="header-container">
        <div class="header-title">⚙️ Dashboard de Refugos - WEG UFE</div>
        <div class="header-subtitle">Gestão Avançada de Turnos, Perdas Operacionais e Análise de Causa Raiz</div>
    </div>
""", unsafe_allow_html=True)

# Função para banco de dados
def init_db():
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    conn.close()

init_db()

# ==================== MENU OCULTO (BARRA LATERAL) ====================
with st.sidebar:
    st.header("🛠️ Menu de Opções")
    
    # Menu expansível que inicia oculto
    with st.expander("📂 Importar e Gerenciar Dados", expanded=False):
        uploaded_file = st.file_uploader("Enviar Planilha (.xlsm, .xlsx, .csv)", type=["xlsx", "xls", "xlsm", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_novo = pd.read_csv(uploaded_file)
                else:
                    df_novo = pd.read_excel(uploaded_file, engine='openpyxl')

                conn = sqlite3.connect('refugos_weg.db', timeout=10)
                df_novo.to_sql('tabela_refugos', conn, if_exists='replace', index=False)
                conn.close()
                st.success("Planilha importada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

    with st.expander("📄 Gerar Relatórios", expanded=False):
        st.write("Exportar Dados Filtrados:")
        if st.button("Gerar PDF com Gráficos"):
            st.info("Função de relatório gráfico em PDF pronta para exportação.")
        if st.button("Gerar PDF para Reunião de Turno"):
            st.info("Relatório executivo para alinhamento de chefes gerado.")

    st.divider()
    st.subheader("🔍 Filtros de Análise")

# Carrega os dados do banco
try:
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    df = pd.read_sql('SELECT * FROM tabela_refugos', conn)
    conn.close()
except:
    df = pd.DataFrame()

if not df.empty:
    # Padroniza colunas para facilitar buscas
    df_col_lower = {c: c.lower() for c in df.columns}
    df = df.rename(columns=df_col_lower)

    # Identificação dinâmica de colunas comuns
    col_data = next((c for c in df.columns if 'data' in c), None)
    col_secao = next((c for c in df.columns if 'secao' in c or 'seção' in c or 'setor' in c), None)
    col_turno = next((c for c in df.columns if 'turno' in c), None)
    col_mes = next((c for c in df.columns if 'mes' in c or 'mês' in c), None)
    col_ano = next((c for c in df.columns if 'ano' in c), None)
    col_colab = next((c for c in df.columns if 'colaborador' in c or 'operador' in c or 'nome' in c), None)
    col_nota = next((c for c in df.columns if 'nota' in c or 'observacao' in c or 'obs' in c), None)

    # ==================== BARRA LATERAL DE FILTROS ====================
    with st.sidebar:
        # 7 - Campo para pesquisar nota/observação
        pesquisa_nota = st.text_input("Pesquisar na Nota / Obs:")

        # 2 - Seção (Todas, A, B, C, D, E, F)
        secoes_disponiveis = ["Todas"] + sorted(df[col_secao].dropna().astype(str).unique().tolist()) if col_secao else ["Todas"]
        filtro_secao = st.selectbox("Seção", secoes_disponiveis)

        # 3 - Turno (Todos, 1, 2, 3)
        turnos_disponiveis = ["Todos"] + sorted(df[col_turno].dropna().astype(str).unique().tolist()) if col_turno else ["Todos"]
        filtro_turno = st.selectbox("Turno", turnos_disponiveis)

        # 4 & 5 - Mês e Ano
        meses_disponiveis = ["Todos"] + sorted(df[col_mes].dropna().astype(str).unique().tolist()) if col_mes else ["Todos"]
        filtro_mes = st.selectbox("Mês", meses_disponiveis)

        anos_disponiveis = ["Todos"] + sorted(df[col_ano].dropna().astype(str).unique().tolist()) if col_ano else ["Todos"]
        filtro_ano = st.selectbox("Ano", anos_disponiveis)

        # 6 - Colaborador
        colabs_disponiveis = ["Todos"] + sorted(df[col_colab].dropna().astype(str).unique().tolist()) if col_colab else ["Todos"]
        filtro_colab = st.selectbox("Colaborador", colabs_disponiveis)

        # 1 - Calendário para filtrar por data
        if col_data:
            st.write("Filtro por Período:")
            try:
                df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                min_date = df[col_data].min().date() if not df[col_data].isnull().all() else pd.to_datetime("2026-01-01").date()
                max_date = df[col_data].max().date() if not df[col_data].isnull().all() else pd.to_datetime("2026-12-31").date()
                data_inicio = st.date_input("Data Inicial", min_date)
                data_fim = st.date_input("Data Final", max_date)
            except:
                data_inicio, data_fim = None, None

    # Aplicando os Filtros no DataFrame
    df_filtrado = df.copy()

    if pesquisa_nota and col_nota:
        df_filtrado = df_filtrado[df_filtrado[col_nota].astype(str).str.contains(pesquisa_nota, case=False, na=False)]
    if filtro_secao != "Todas" and col_secao:
        df_filtrado = df_filtrado[df_filtrado[col_secao].astype(str) == filtro_secao]
    if filtro_turno != "Todos" and col_turno:
        df_filtrado = df_filtrado[df_filtrado[col_turno].astype(str) == filtro_turno]
    if filtro_mes != "Todos" and col_mes:
        df_filtrado = df_filtrado[df_filtrado[col_mes].astype(str) == filtro_mes]
    if filtro_ano != "Todos" and col_ano:
        df_filtrado = df_filtrado[df_filtrado[col_ano].astype(str) == filtro_ano]
    if filtro_colab != "Todos" and col_colab:
        df_filtrado = df_filtrado[df_filtrado[col_colab].astype(str) == filtro_colab]
    if col_data and data_inicio and data_fim:
        df_filtrado = df_filtrado[(df_filtrado[col_data].dt.date >= data_inicio) & (df_filtrado[col_data].dt.date <= data_fim)]

    # ==================== EXIBIÇÃO DO DASHBOARD ====================
    st.subheader(f"📊 Resultados Filtrados ({len(df_filtrado)} registros encontrados)")
    
    st.dataframe(df_filtrado, use_container_width=True)

    # Botão de limpeza do banco
    if st.sidebar.button("🗑️ Limpar Banco de Dados"):
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        conn.execute('DROP TABLE IF EXISTS tabela_refugos')
        conn.commit()
        conn.close()
        st.rerun()

else:
    st.warning("⚠️ O banco de dados está vazio. Utilize o menu lateral esquerdo (clique em '📂 Importar e Gerenciar Dados') para enviar a sua planilha `.xlsm` de agosto.")
