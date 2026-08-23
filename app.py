import streamlit as st
import pandas as pd
import sqlite3

# Configuração da página
st.set_page_config(page_title="Dashboard Refugos - WEG UFE", layout="wide")

st.title("⚠️ Dashboard Refugos - WEG UFE")
st.caption("Monitoramento de perdas operacionais com Banco de Dados Flexível")

# Seção de Importação no Menu Lateral
uploaded_file = st.sidebar.file_uploader("Importar planilha (.xlsm, .xlsx, .csv)", type=["xlsx", "xls", "xlsm", "csv"])

if uploaded_file is not None:
    try:
        # Lê o arquivo Excel (com suporte a macros via openpyxl) ou CSV
        if uploaded_file.name.endswith('.csv'):
            df_novo = pd.read_csv(uploaded_file)
        else:
            df_novo = pd.read_excel(uploaded_file, engine='openpyxl')

        # Salva exatamente a estrutura da planilha no banco de dados SQLite
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        df_novo.to_sql('tabela_refugos', conn, if_exists='replace', index=False)
        conn.close()
        
        st.sidebar.success("Planilha importada e salva no banco de dados com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao ler ou salvar o arquivo: {e}")

# Tenta carregar os dados salvos no banco
try:
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    df = pd.read_sql('SELECT * FROM tabela_refugos', conn)
    conn.close()
except:
    df = pd.DataFrame()

if not df.empty:
    # Exibe a tabela completa exatamente como veio da sua planilha com macros
    st.subheader("Dados Armazenados no Banco Local")
    st.dataframe(df, use_container_width=True)

    # Botão para limpar o banco de dados
    if st.button("Limpar Banco de Dados"):
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        conn.execute('DROP TABLE IF EXISTS tabela_refugos')
        conn.commit()
        conn.close()
        st.rerun()

else:
    st.info("O banco de dados está vazio. Faça o upload da sua planilha de agosto no menu lateral.")
