import streamlit as st
import pandas as pd
import sqlite3

# Configuração da página
st.set_page_config(page_title="Dashboard Refugos - WEG UFE", layout="wide")

# Função para conectar e criar o banco de dados local
def init_db():
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refugos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            turno TEXT,
            maquina TEXT,
            qtd_produzida REAL,
            qtd_refugada REAL,
            motivo TEXT,
            custo_unitario REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.title("⚠️ Dashboard Refugos - WEG UFE")
st.caption("Monitoramento de perdas operacionais e análise de causa raiz com Banco de Dados")

# Seção de Importação no Menu Lateral
uploaded_file = st.sidebar.file_uploader("Importar planilha de dados", type=["xlsx", "xls", "xlsm", "csv"])

if uploaded_file is not None:
    try:
        # Lê o arquivo dependendo da extensão
        if uploaded_file.name.endswith('.csv'):
            df_novo = pd.read_csv(uploaded_file)
        else:
            # engine='openpyxl' garante leitura correta de arquivos .xlsx e .xlsm
            df_novo = pd.read_excel(uploaded_file, engine='openpyxl')

        # Padroniza os nomes das colunas para minúsculo
        df_novo.columns = [str(c).strip().lower() for c in df_novo.columns]

        # Conecta ao banco de dados e salva os dados novos
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        df_novo.to_sql('refugos', conn, if_exists='append', index=False)
        conn.close()
        
        st.sidebar.success("Planilha importada e salva no banco de dados com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro detalhado ao processar o arquivo: {e}")

# Carrega os dados usando uma query SQL segura
try:
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    df = pd.read_sql('SELECT * FROM refugos', conn)
    conn.close()
except:
    df = pd.DataFrame()

if not df.empty:
    # Remove a coluna ID gerada pelo banco para exibição limpa
    if 'id' in df.columns:
        df_exibicao = df.drop(columns=['id'])
    else:
        df_exibicao = df

    # Normaliza nomes de colunas para os cálculos
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Identifica colunas de forma flexível
    col_prod = next((c for c in df.columns if 'produzida' in c or 'prod' in c), None)
    col_ref = next((c for c in df.columns if 'refugada' in c or 'ref' in c), None)
    col_custo = next((c for c in df.columns if 'custo' in c), None)
    col_motivo = next((c for c in df.columns if 'motivo' in c or 'defeito' in c), None)
    col_data = next((c for c in df.columns if 'data' in c), None)

    total_produzido = df[col_prod].sum() if col_prod else 0
    total_refugado = df[col_ref].sum() if col_ref else 0
    
    if col_custo and col_ref:
        custo_total = (df[col_ref] * df[col_custo]).sum()
    else:
        custo_total = 0
        
    taxa_refugo = (total_refugado / total_produzido * 100) if total_produzido > 0 else 0

    # Exibição dos KPIs em Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Refugado", f"{total_refugado:,.0f} pçs".replace(",", "."))
    col2.metric("Taxa de Refugo Geral", f"{taxa_refugo:.2f}%")
    col3.metric("Custo Total", f"R$ {custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col4.metric("Total Produzido", f"{total_produzido:,.0f} pçs".replace(",", "."))

    st.divider()

    # Gráficos
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Motivos de Refugo")
        if col_motivo and col_ref:
            pareto_df = df.groupby(col_motivo)[col_ref].sum().reset_index().sort_values(by=col_ref, ascending=False)
            st.bar_chart(pareto_df.set_index(col_motivo))

    with c2:
        st.subheader("Evolução Temporal")
        if col_data and col_ref:
            trend_df = df.groupby(col_data)[col_ref].sum().reset_index()
            st.line_chart(trend_df.set_index(col_data))

    st.divider()

    # Tabela detalhada com os dados salvos no banco
    st.subheader("Banco de Dados Operacional (Histórico Salvo)")
    st.dataframe(df_exibicao, use_container_width=True)

    # Botão para limpar o banco de dados caso precise reiniciar os testes
    if st.button("Limpar Banco de Dados"):
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        conn.execute('DELETE FROM refugos')
        conn.commit()
        conn.close()
        st.rerun()

else:
    st.info("O banco de dados está vazio. Faça o upload da sua planilha pelo menu lateral para começar a registrar os dados.")
