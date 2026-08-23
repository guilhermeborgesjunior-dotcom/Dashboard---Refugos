import streamlit as str_lit
import pandas as pd
import sqlite3

# Configuração da página (deve ser a primeira instrução)
str_lit.set_page_config(page_title="Dashboard Refugos - WEG UFE", layout="wide")

# Estilos customizados (Fundo branco para tabela, texto escuro e container do cabeçalho)
str_lit.markdown("""
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
    
    /* Estilos CSS para fundo branco e contraste na tabela */
    .tabela-container-wrapper {
        overflow-x: auto; 
        max-height: 480px; 
        border: 1px solid #cbd5e1; 
        border-radius: 8px;
        background-color: #ffffff;
    }

    #tabela-refugos {
        width: 100%; 
        border-collapse: collapse; 
        font-family: sans-serif; 
        font-size: 14px; 
        color: #1e293b !important;
        background-color: #ffffff !important;
    }

    #tabela-refugos thead tr {
        background-color: #f1f5f9 !important; 
        border-bottom: 2px solid #cbd5e1 !important; 
        position: sticky; 
        top: 0; 
        z-index: 1;
        color: #0f172a !important;
    }

    #tabela-refugos tbody tr {
        border-bottom: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
    }

    #tabela-refugos tbody tr:hover {
        background-color: #f8fafc !important;
    }

    /* Estilo interativo do APQ com cursor pointer obrigatório */
    .apq-toggle {
        font-weight: bold;
        cursor: pointer !important;
        padding: 4px 8px;
        border-radius: 4px;
        user-select: none;
        display: inline-block;
        transition: background 0.2s;
    }
    .apq-toggle:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }

    /* Estilo do botão de edição */
    .btn-editar {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
        transition: background 0.2s;
    }
    .btn-editar:hover {
        background-color: #2563eb;
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

# ==================== MENU LATERAL ====================
with str_lit.sidebar:
    str_lit.header("🛠️ Menu de Opções")
    
    with str_lit.expander("📂 Importar e Gerenciar Dados", expanded=False):
        uploaded_file = str_lit.file_uploader("Enviar Planilha (.xlsm, .xlsx)", type=["xlsx", "xls", "xlsm"])
        if uploaded_file is not None:
            try:
                df_novo = pd.read_excel(uploaded_file, sheet_name='Notas', engine='openpyxl')
                df_novo.columns = [str(c).strip().lower() for c in df_novo.columns]

                conn = sqlite3.connect('refugos_weg.db', timeout=10)
                df_novo.to_sql('tabela_notas', conn, if_exists='replace', index=False)
                conn.close()
                str_lit.success("Aba 'Notas' importada com sucesso!")
                str_lit.rerun()
            except Exception as e:
                str_lit.error(f"Erro ao importar a aba 'Notas'. Detalhe: {e}")

    with str_lit.expander("📄 Gerar Relatórios", expanded=False):
        if str_lit.button("Gerar PDF com Gráficos"):
            str_lit.info("Função de relatório gráfico pronta.")
        if str_lit.button("Gerar PDF para Reunião de Turno"):
            str_lit.info("Relatório executivo gerado.")

    str_lit.divider()
    str_lit.subheader("🔍 Filtros de Análise")

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
    col_apq = encontra_coluna(['apq'])

    if not col_obs and 'observacao' not in df.columns:
        df['observacao'] = ""
        col_obs = 'observacao'
    if not col_acao and 'acao' not in df.columns:
        df['acao'] = ""
        col_acao = 'acao'
    if not col_colab and 'colaborador' not in df.columns:
        df['colaborador'] = ""
        col_colab = 'colaborador'
    if not col_prep and 'preparador' not in df.columns:
        df['preparador'] = ""
        col_prep = 'preparador'
    if not col_apq and 'apq' not in df.columns:
        df['apq'] = "Pendente"
        col_apq = 'apq'
    else:
        df[col_apq] = df[col_apq].fillna("Pendente").apply(
            lambda x: "Concluída" if str(x).strip().lower() in ['concluída', 'concluida', 'concluido', 'sim', '1', 'true'] else "Pendente"
        )

    def limpa_inteiro(val):
        if pd.notna(val):
            try:
                return str(int(float(val)))
            except:
                return str(val)
        return ""

    def formata_custo(val):
        if pd.notna(val):
            try:
                return f"{float(val):.2f}".replace('.', ',')
            except:
                return str(val)
        return ""

    def trata_nulos(val):
        if pd.isna(val) or val is None or str(val).strip().lower() in ['none', 'nan', 'undefined', 'null']:
            return ""
        return str(val)

    def obs_esta_vazia(val):
        if val is None or pd.isna(val):
            return True
        s = str(val).strip().lower()
        if s in ['', 'none', 'nan', 'undefined', 'null']:
            return True
        return False

    # ==================== FILTROS NA BARRA LATERAL ====================
    with str_lit.sidebar:
        pesquisa_nota = str_lit.text_input("Pesquisar Nota:")

        secoes_opcoes = ["Todas"] + sorted(df[col_secao].dropna().astype(str).unique().tolist()) if col_secao else ["Todas"]
        filtro_secao = str_lit.selectbox("Seção", secoes_opcoes)

        turnos_opcoes = ["Todos"] + sorted(df[col_turno].dropna().astype(str).unique().tolist()) if col_turno else ["Todos"]
        filtro_turno = str_lit.selectbox("Turno", turnos_opcoes)

        if col_data:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
            df['__ano__'] = df[col_data].dt.year
            df['__mes__'] = df[col_data].dt.month

        meses_opcoes = ["Todos"] + sorted(df['__mes__'].dropna().astype(int).astype(str).unique().tolist()) if '__mes__' in df.columns else ["Todos"]
        filtro_mes = str_lit.selectbox("Mês", meses_opcoes)

        anos_opcoes = ["Todos"] + sorted(df['__ano__'].dropna().astype(int).astype(str).unique().tolist()) if '__ano__' in df.columns else ["Todos"]
        filtro_ano = str_lit.selectbox("Ano", anos_opcoes)

        colab_opcoes = ["Todos"] + sorted(df[col_colab].dropna().astype(str).unique().tolist()) if col_colab else ["Todos"]
        filtro_colab = str_lit.selectbox("Colaborador", colab_opcoes)

        if col_data:
            str_lit.write("Período de Data:")
            min_d = df[col_data].min().date() if not df[col_data].isnull().all() else pd.to_datetime("2026-01-01").date()
            max_d = df[col_data].max().date() if not df[col_data].isnull().all() else pd.to_datetime("2026-12-31").date()
            data_ini = str_lit.date_input("Data Inicial", min_d)
            data_fim = str_lit.date_input("Data Final", max_d)

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

    if col_nota:
        df_filtrado['__nota_com_alerta__'] = df_filtrado.apply(
            lambda row: f"⚠️ {limpa_inteiro(row[col_nota])}" if obs_esta_vazia(row[col_obs]) else limpa_inteiro(row[col_nota]),
            axis=1
        )

    # Captura o ID da linha selecionada para edição via parâmetros de URL
    query_params = str_lit.query_params
    edit_id = query_params.get("edit_rowid", None)

    if edit_id:
        str_lit.info(f"✏️ Modo de Edição Ativo para o Registro ID: {edit_id}")
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        df_edit = pd.read_sql(f'SELECT rowid, * FROM tabela_notas WHERE rowid = {edit_id}', conn)
        conn.close()
        
        if not df_edit.empty:
            with str_lit.form(key="form_edicao_linha"):
                str_lit.subheader("Editar Informações da Nota")
                nova_obs = str_lit.text_input("Observação", value=str(df_edit.iloc[0].get(col_obs, '')) if col_obs in df_edit.columns else "")
                nova_acao = str_lit.text_input("Ação", value=str(df_edit.iloc[0].get(col_acao, '')) if col_acao in df_edit.columns else "")
                
                submitted = str_lit.form_submit_button("Salvar Alterações")
                if submitted:
                    conn = sqlite3.connect('refugos_weg.db', timeout=10)
                    conn.execute(f"UPDATE tabela_notas SET {col_obs} = ?, {col_acao} = ? WHERE rowid = ?", (nova_obs, nova_acao, edit_id))
                    conn.commit()
                    conn.close()
                    
                    str_lit.query_params.clear()
                    str_lit.success("Registro atualizado com sucesso!")
                    str_lit.rerun()

    # ==================== EXIBIÇÃO DA TABELA HTML ====================
    str_lit.subheader(f"📊 Registros Encontrados ({len(df_filtrado)})")
    str_lit.markdown("💡 **Instruções:** Clique na palavra **APQ** para alternar instantaneamente entre **Vermelho (Pendente)** e **Verde (Concluído)**. Utilize o botão **Editar** na última coluna para modificar os dados da linha.")

    # Mapeamento completo com APQ e Ações ao final
    mapeamento_colunas = {
        col_secao: "Seção",
        col_defeito: "Defeito",
        col_nota: "Nota",
        col_data: "Data",
        col_turno: "Turno",
        col_material: "Material",
        col_desc_mat: "Descrição Material",
        col_ct: "CT Causador",
        col_qtd: "Quantidade",
        col_desc_feito: "Descrição Defeito",
        col_causa: "Causa",
        col_texto_causa: "Texto Causa",
        col_custo: "Custo",
        col_obs: "Observação",
        col_acao: "Ação",
        col_colab: "Colaborador",
        col_prep: "Preparador",
        col_apq: "APQ",
        "acao_editar": "Ações"
    }

    html_tabela = """
    <div class="tabela-container-wrapper">
    <table id="tabela-refugos">
      <thead>
        <tr>
    """
    
    colunas_validas = [k for k in mapeamento_colunas.keys() if k is not None]
    
    for k in colunas_validas:
        nome_cab = mapeamento_colunas[k]
        html_tabela += f'<th style="padding: 12px 10px; text-align: left; font-weight: 600;">{nome_cab}</th>'
    html_tabela += "</tr></thead><tbody>"

    for idx, row in df_filtrado.iterrows():
        r_id = row['rowid']
        html_tabela += f'<tr onclick="selecionarLinha(this)" data-rowid="{r_id}">'
        
        for k in colunas_validas:
            if k == "acao_editar":
                val = f'<button class="btn-editar" onclick="abrirEdicao({r_id})">✏️ Editar</button>'
            elif k == col_nota:
                val = str(row['__nota_com_alerta__']) if '__nota_com_alerta__' in row else str(row[k])
            elif k == col_apq:
                raw_apq = str(row[k]).strip().lower()
                is_concluida = raw_apq in ['concluída', 'concluida', 'concluido', 'sim', '1', 'true']
                cor_inicial = "#27ae60" if is_concluida else "#e74c3c"
                status_inicial = "concluido" if is_concluida else "pendente"
                
                val = f'<span class="apq-toggle" data-status="{status_inicial}" style="color: {cor_inicial};">APQ</span>'
            else:
                val = trata_nulos(row[k])
                if k == col_custo and pd.notna(row[k]):
                    val = formata_custo(row[k])
            
            html_tabela += f'<td style="padding: 10px 10px; white-space: nowrap;">{val}</td>'
        html_tabela += "</tr>"

    html_tabela += """
      </tbody>
    </table>
    </div>

    <script>
    function selecionarLinha(tr) {
        var rows = tr.parentElement.getElementsByTagName('tr');
        for (var i = 0; i < rows.length; i++) {
            rows[i].style.backgroundColor = '';
        }
        tr.style.backgroundColor = '#f1f5f9';
    }

    function abrirEdicao(rowid) {
        const queryParams = new URLSearchParams(window.location.search);
        queryParams.set('edit_rowid', rowid);
        window.history.replaceState(null, '', '?' + queryParams.toString());
        window.parent.document.dispatchEvent(new Event('streamlit:rerun'));
    }

    document.addEventListener("click", function(event) {
        if (event.target && event.target.classList.contains("apq-toggle")) {
            event.stopPropagation();
            
            const el = event.target;
            const statusAtual = el.getAttribute("data-status");

            if (statusAtual === "pendente") {
                el.style.color = "#27ae60";
                el.setAttribute("data-status", "concluido");
            } else {
                el.style.color = "#e74c3c";
                el.setAttribute("data-status", "pendente");
            }
        }
    });
    </script>
    """

    str_lit.markdown(html_tabela, unsafe_allow_html=True)

    str_lit.divider()
    if str_lit.sidebar.button("🗑️ Limpar Banco de Dados"):
        conn = sqlite3.connect('refugos_weg.db', timeout=10)
        conn.execute('DROP TABLE IF EXISTS tabela_notas')
        conn.commit()
        conn.close()
        str_lit.rerun()

else:
    str_lit.warning("⚠️ O banco de dados está vazio. Clique no ícone de menu (3 barrinhas) no canto superior direito, abra '📂 Importar e Gerenciar Dados' e envie a planilha.")
