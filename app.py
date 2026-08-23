import streamlit as st
import pandas as pd
import sqlite3

# Configuração da página (deve ser a primeira instrução)
st.set_page_config(page_title="Dashboard Refugos - WEG UFE", layout="wide")

# Estilos customizados para largura total, cabeçalho e menu hamburger no canto superior direito
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    .header-container {
        position: relative;
        background-image: linear-gradient(rgba(10, 25, 47, 0.88), rgba(10, 25, 47, 0.88)), 
                          url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        padding: 35px 40px;
        border-radius: 0px 0px 12px 12px;
        color: white;
        margin-left: -2rem;
        margin-right: -2rem;
        margin-top: -4rem;
        margin-bottom: 20px;
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

    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 15px !important;
        right: 20px !important;
        z-index: 999999 !important;
        background-color: #0a192f !important;
        border-radius: 5px;
        color: white !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: white !important;
    }
    </style>
    
    <div class="header-container">
        <div class="header-title">⚙️ Dashboard de Refugos - WEG UFE</div>
        <div class="header-subtitle">Gestão de Apontamentos da Aba "Notas" e Perdas Operacionais</div>
    </div>
""", unsafe_allow_html=True)

# Inicializa o banco de dados
def init_db():
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    conn.close()

init_db()

# ==================== MENU LATERAL (OCULTO / HAMBÚRGUER DIREITO) ====================
with st.sidebar:
    st.header("🛠️ Menu de Opções")
    
    with st.expander("📂 Importar e Gerenciar Dados", expanded=False):
        uploaded_file = st.file_uploader("Enviar Planilha (.xlsm, .xlsx)", type=["xlsx", "xls", "xlsm"])
        if uploaded_file is not None:
            try:
                df_novo = pd.read_excel(uploaded_file, sheet_name='Notas', engine='openpyxl')
                df_novo.columns = [str(c).strip().lower() for c in df_novo.columns]

                conn = sqlite3.connect('refugos_weg.db', timeout=10)
                df_novo.to_sql('tabela_notas', conn, if_exists='replace', index=False)
                conn.close()
                st.success("Aba 'Notas' importada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar a aba 'Notas'. Detalhe: {e}")

    with st.expander("📄 Gerar Relatórios", expanded=False):
        if st.button("Gerar PDF com Gráficos"):
            st.info("Função de relatório gráfico pronta.")
        if st.button("Gerar PDF para Reunião de Turno"):
            st.info("Relatório executivo gerado.")

    st.divider()
    st.subheader("🔍 Filtros de Análise")

# Carrega os dados do banco
try:
    conn = sqlite3.connect('refugos_weg.db', timeout=10)
    df = pd.read_sql('SELECT rowid, * FROM tabela_notas', conn)
    conn.close()
except:
    df = pd.DataFrame()

if not df.empty:
    cols_normalizadas = {c: ('rowid' if c == 'rowid' else str(c).strip().lower()) for c in df.columns}
    df = df.rename(columns=cols_normalizadas)

    def encontra_coluna(termos):
        for t in termos:
            for c in df.columns:
                if t in c:
                    return c
        return None

    col_secao = encontra_coluna(['seção', 'secao'])
    col_defeito = encontra_coluna(['defeito'])
    col_nota = encontra_coluna(['nota'])
    col_data = encontra_coluna(['data'])
    col_turno = encontra_coluna(['turno'])
    col_material = encontra_coluna(['material'])
    col_desc_mat = encontra_coluna(['descrição do material', 'descricao do material'])
    col_ct = encontra_coluna(['ct causador'])
    col_qtd = encontra_coluna(['quantidade'])
    col_desc_feito = encontra_coluna(['descrição do feito', 'descricao do feito', 'descrição do defeito', 'descricao do defeito'])
    col_causa = encontra_coluna(['causa'])
    col_texto_causa = encontra_coluna(['texto da causa'])
    col_custo = encontra_coluna(['custo'])
    col_obs = encontra_coluna(['observaçao', 'observacao', 'informacoes', 'informações'])
    col_acao = encontra_coluna(['ação', 'acao'])
    col_colab = encontra_coluna(['colaborador', 'colcaborador'])
    col_prep = encontra_coluna(['preparador'])

    # ==================== FILTROS NA BARRA LATERAL ====================
    with st.sidebar:
        pesquisa_nota = st.text_input("Pesquisar Nota:")

        secoes_opcoes = ["Todas"] + sorted(df[col_secao].dropna().astype(str).unique().tolist()) if col_secao else ["Todas"]
        filtro_secao = st.selectbox("Seção", secoes_opcoes)

        turnos_opcoes = ["Todos"] + sorted(df[col_turno].dropna().astype(str).unique().tolist()) if col_turno else ["Todos"]
        filtro_turno = st.selectbox("Turno", turnos_opcoes)

        if col_data:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
            df['__ano__'] = df[col_data].dt.year
            df['__mes__'] = df[col_data].dt.month

        meses_opcoes = ["Todos"] + sorted(df['__mes__'].dropna().astype(int).astype(str).unique().tolist()) if '__mes__' in df.columns else ["Todos"]
        filtro_mes = st.selectbox("Mês", meses_opcoes)

        anos_opcoes = ["Todos"] + sorted(df['__ano__'].dropna().astype(int).astype(str).unique().tolist()) if '__ano__' in df.columns else ["Todos"]
        filtro_ano = st.selectbox("Ano", anos_opcoes)

        colab_opcoes = ["Todos"] + sorted(df[col_colab].dropna().astype(str).unique().tolist()) if col_colab else ["Todos"]
        filtro_colab = st.selectbox("Colaborador", colab_opcoes)

        if col_data:
            st.write("Período de Data:")
            min_d = df[col_data].min().date() if not df[col_data].isnull().all() else pd.to_datetime("2026-01-01").date()
            max_d = df[col_data].max().date() if not df[col_data].isnull().all() else pd.to_datetime("2026-12-31").date()
            data_ini = st.date_input("Data Inicial", min_d)
            data_fim = st.date_input("Data Final", max_d)

    # Aplicando os filtros
    df_filtrado = df.copy()

    if pesquisa_nota and col_nota:
        df_filtrado = df_filtrado[df_filtrado[col_nota].astype(str).str.contains(pesquisa_nota, case=False, na=False)]
    if filtro_secao != "Todas" and col_secao:
        df_filtrado = df_filtrado[df_filtrado[col_secao].astype(str) == filtro_secao]
    if filtro_turno != "Todos" and col_turno:
        df_filtrado = df_filtrado[df_filtrado[col_turno].astype(str) == filtro_turno]
    if filtro_mes != "Todos" and '__mes__' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['__mes__'].astype(str) == filtro_mes]
    if filtro_ano != "Todos" and '__ano__' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['__ano__'].astype(str) == filtro_ano]
    if filtro_colab != "Todos" and col_colab:
        df_filtrado = df_filtrado[df_filtrado[col_colab].astype(str) == filtro_colab]
    if col_data and 'data_ini' in locals() and 'data_fim' in locals():
        df_filtrado = df_filtrado[(df_filtrado[col_data].dt.date >= data_ini) & (df_filtrado[col_data].dt.date <= data_fim)]

    # ==================== POP-UP DE EDIÇÃO EM MODAL (ST.DIALOG) ====================
    @st.dialog("✏️ Editar Registro da Nota", width="large")
    def modal_edicao(rowid_alvo):
        linha_atual = df[df['rowid'] == rowid_alvo].iloc[0]
        
        st.markdown(f"### Nota: `{linha_atual[col_nota] if col_nota else 'N/A'}` | Seção: `{linha_atual[col_secao] if col_secao else 'N/A'}`")
        st.write("Utilize as abas abaixo para editar as informações:")

        with st.form(f"form_modal_{rowid_alvo}"):
            aba_info, aba_acao, aba_colab, aba_prep = st.tabs(["Informações", "Ação", "Colaborador", "Preparador"])

            with aba_info:
                val_obs = str(linha_atual[col_obs]) if col_obs and pd.notna(linha_atual[col_obs]) else ""
                novo_obs = st.text_area("Informações (Observação):", value=val_obs, height=120)

            with aba_acao:
                val_acao = str(linha_atual[col_acao]) if col_acao and pd.notna(linha_atual[col_acao]) else ""
                nova_acao = st.text_input("Ação corretiva/operacional:", value=val_acao)

            with aba_colab:
                val_colab = str(linha_atual[col_colab]) if col_colab and pd.notna(linha_atual[col_colab]) else ""
                novo_colab = st.text_input("Colaborador responsável:", value=val_colab)

            with aba_prep:
                val_prep = str(linha_atual[col_prep]) if col_prep and pd.notna(linha_atual[col_prep]) else ""
                novo_prep = st.text_input("Preparador responsável:", value=val_prep)

            st.write("")
            salvar = st.form_submit_button("💾 Salvar Alterações", type="primary")
            
            if salvar:
                try:
                    conn = sqlite3.connect('refugos_weg.db', timeout=10)
                    cursor = conn.cursor()
                    
                    updates = []
                    params = []
                    if col_obs:
                        updates.append(f"{col_obs} = ?")
                        params.append(novo_obs)
                    if col_acao:
                        updates.append(f"{col_acao} = ?")
                        params.append(nova_acao)
                    if col_colab:
                        updates.append(f"{col_colab} = ?")
                        params.append(novo_colab)
                    if col_prep:
                        updates.append(f"{col_prep} = ?")
                        params.append(novo_prep)
                    
                    params.append(rowid_alvo)
                    query = f"UPDATE tabela_notas SET {', '.join(updates)} WHERE rowid = ?"
                    
                    cursor.execute(query, params)
                    conn.commit()
                    conn.close()
                    
                    st.success("Atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # ==================== EXIBIÇÃO DA TABELA ÚNICA COM CABEÇALHO CONGELADO ====================
    st.subheader(f"📊 Registros Encontrados ({len(df_filtrado)})")

    mapeamento_colunas = {
        col_secao: "seção",
        col_defeito: "defeito",
        col_nota: "nota",
        col_data: "data",
        col_turno: "turno",
        col_material: "material",
        col_desc_mat: "descrição do material",
        col_ct: "ct causador",
        col_qtd: "quantidade",
        col_desc_feito: "descrição do defeito",
        col_causa: "causa",
        col_texto_causa: "texto da causa",
        col_custo: "custo",
        col_obs: "informações",
        col_acao: "ação",
        col_colab: "colaborador",
        col_prep: "preparador"
    }

    colunas_presentes = ['rowid'] + [k for k in mapeamento_colunas.keys() if k is not None]
    df_exibicao = df_filtrado[colunas_presentes].rename(columns=mapeamento_colunas)

    # Criamos uma coluna visual extra para o botão de edição direto na tabela unificada
    col_acoes_acoes = []
    for r_id in df_exibicao['rowid']:
        col_acoes_acoes.append("✏️ Editar")
    
    df_exibicao['Ações'] = col_acoes_acoes

    # Exibe a tabela completa em um único bloco com altura fixa (ativa o sticky header nativo e rolagem interna)
    evento_selecao = st.dataframe(
        df_exibicao.drop(columns=['rowid']),
        use_container_width=True,
        hide_index=True,
        height=450,
        selection_mode="single-row",
        on_select="rerun"
    )

    # Se o usuário clicar em uma linha ou quisermos dar suporte via seleção na tabela nativa:
    # Como alternativa prática e direta para abrir o pop-up da linha selecionada:
    if evento_selecao and evento_selecao.selection.rows:
        linha_selecionada_idx = evento_selecao.selection.rows[0]
        r_id_selecionado = df_exibicao.iloc[linha_selecionada_idx]['rowid']
        modal_edicao(r_id_selecionado)

    # Botão de limpeza do banco
    if st.sidebar.button("🗑️ Limpar Banco de Dados"):
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        conn.execute('DROP TABLE IF EXISTS tabela_notas')
        conn.commit()
        conn.close()
        st.rerun()

else:
    st.warning("⚠️ O banco de dados está vazio. Clique no ícone de menu (3 barrinhas) no canto superior direito, abra '📂 Importar e Gerenciar Dados' e envie a planilha.")
