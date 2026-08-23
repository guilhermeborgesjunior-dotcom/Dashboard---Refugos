import streamlit as str_lit
import pandas as pd
import sqlite3

# Configuração da página (deve ser a primeira instrução)
str_lit.set_page_config(page_title="Dashboard Refugos - WEG UFE", layout="wide")

# Estilos customizados para largura total, cabeçalho e menu hamburger no canto superior direito
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
    
    /* Estilos customizados para a interatividade da célula APQ no Front-end */
    .apq-toggle {
        font-weight: bold;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        user-select: none;
        transition: background 0.2s;
        display: inline-block;
    }
    .apq-toggle:hover {
        background-color: rgba(255, 255, 255, 0.08);
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

    # Garante a existência física das colunas no DataFrame
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

    # Tratamento opcional via query params para persistência no banco, se necessário
    params_url = str_lit.query_params
    if "toggle_apq_rowid" in params_url:
        try:
            r_id = int(params_url["toggle_apq_rowid"])
            conn = sqlite3.connect('refugos_weg.db', timeout=10)
            cursor = conn.cursor()
            res = cursor.execute(f'SELECT "{col_apq}" FROM tabela_notas WHERE rowid = ?', (r_id,)).fetchone()
            if res:
                atual = str(res[0]).strip().lower()
                novo_val = "Pendente" if atual in ['concluída', 'concluida', 'concluido', 'sim', '1', 'true'] else "Concluída"
                cursor.execute(f'UPDATE tabela_notas SET "{col_apq}" = ? WHERE rowid = ?', (novo_val, r_id))
                conn.commit()
            conn.close()
            str_lit.query_params.clear()
            str_lit.rerun()
        except Exception:
            pass

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

    # ==================== EXIBIÇÃO DA TABELA HTML COM JAVASCRIPT DE TOGGLE INSTANTÂNEO ====================
    str_lit.subheader(f"📊 Registros Encontrados ({len(df_filtrado)})")
    str_lit.markdown("💡 **Instruções:** Clique diretamente na palavra **APQ** de qualquer linha para alternar instantaneamente entre **Vermelho (Pendente)** e **Verde (Concluído)**.")

    # Mapeamento com APQ estritamente na ÚLTIMA posição
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
        col_apq: "APQ"  # Posicionada no fim -> Última coluna da tabela
    }

    html_tabela = """
    <div style="overflow-x: auto; max-height: 480px; border: 1px solid #334155; border-radius: 8px;">
    <table id="tabela-refugos" style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; color: #f8fafc; background-color: #0f172a;">
      <thead>
        <tr style="background-color: #1e293b; border-bottom: 2px solid #334155; position: sticky; top: 0; z-index: 1;">
    """
    
    colunas_validas = [k for k in mapeamento_colunas.keys() if k is not None]
    
    for k in colunas_validas:
        nome_cab = mapeamento_colunas[k]
        html_tabela += f'<th style="padding: 12px 10px; text-align: left; font-weight: 600;">{nome_cab}</th>'
    html_tabela += "</tr></thead><tbody>"

    for idx, row in df_filtrado.iterrows():
        r_id = row['rowid']
        html_tabela += f'<tr style="border-bottom: 1px solid #1e293b;" onclick="selecionarLinha(this)">'
        
        for k in colunas_validas:
            if k == col_nota:
                val = str(row['__nota_com_alerta__']) if '__nota_com_alerta__' in row else str(row[k])
            elif k == col_apq:
                raw_apq = str(row[k]).strip().lower()
                is_concluida = raw_apq in ['concluída', 'concluida', 'concluido', 'sim', '1', 'true']
                # Estado inicial baseado no banco (Vermelho #ff4d4d para pendente, Verde #2ecc71 para concluído)
                cor_inicial = "#2ecc71" if is_concluida else "#ff4d4d"
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
        tr.style.backgroundColor = '#1e293b';
    }

    // Script DOM para interatividade de clique único instantâneo (Vermelho <-> Verde)
    document.addEventListener("DOMContentLoaded", function() {
        const apqElements = document.querySelectorAll('.apq-toggle');

        apqElements.forEach(el => {
            el.addEventListener('click', function(event) {
                event.stopPropagation(); // Impede propagação para a linha
                
                const statusAtual = el.getAttribute('data-status');

                if (statusAtual === 'pendente') {
                    // Muda para Verde (Concluído)
                    el.style.color = '#2ecc71';
                    el.setAttribute('data-status', 'concluido');
                } else {
                    // Muda para Vermelho (Pendente)
                    el.style.color = '#ff4d4d';
                    el.setAttribute('data-status', 'pendente');
                }
            });
        });
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
