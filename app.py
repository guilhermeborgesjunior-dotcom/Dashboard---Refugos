import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date

# ============================================================
# CONFIGURAÇÃO
# ============================================================
st.set_page_config(
    page_title="Dashboard Refugos - WEG UFE",
    layout="wide",
    initial_sidebar_state="collapsed",
)
DB_PATH = Path("refugos_weg.db")
TABLE_NAME = "tabela_notas"

# ============================================================
# 📋 COLUNAS OFICIAIS — EXATAMENTE AS QUE VOCÊ PEDIU
# ============================================================
COLUNAS_OFICIAIS = [
    "seção",
    "defeito",
    "nota",
    "data",
    "turno",
    "material",
    "descrição do material",
    "ct causador",
    "quantidade",
    "descrição do defeito",
    "causa",
    "texto da causa",
    "custo",
    "observações",
    "ação",
    "colaborador",
    "preparador",
    "apq",
    "twtp",
    "twttp",
]

COLUNAS_IGNORAR = ["dia", "semana", "__ano__", "__mes__"]

# ============================================================
# ESTILO
# ============================================================
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
    background-image:
        linear-gradient(rgba(10,25,47,.88), rgba(10,25,47,.88)),
        url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1600&q=80');
    background-size: cover;
    background-position: center;
    padding: 35px 40px;
    border-radius: 0 0 12px 12px;
    color: white;
    margin-left: -2rem;
    margin-right: -2rem;
    margin-top: -4rem;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,.3);
}
.header-title {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    color: #fff;
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
    <div class="header-subtitle">
        Gestão de Apontamentos da Aba "Notas" e Perdas Operacionais
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# BANCO DE DADOS
# ============================================================
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def table_exists():
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE_NAME,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()

def load_data():
    if not table_exists():
        return pd.DataFrame()
    conn = get_connection()
    try:
        df = pd.read_sql(f'SELECT rowid, * FROM "{TABLE_NAME}"', conn)
        # ✅ REMOVE COLUNAS INDESEJADAS automaticamente
        for col in COLUNAS_IGNORAR:
            if col in df.columns:
                df = df.drop(columns=[col])
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

# ============================================================
# UTILITÁRIOS
# ============================================================
def normalize_columns(df):
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace("\n", " ")
        for c in df.columns
    ]
    return df

def filtrar_colunas_oficiais(df):
    """Mantém SOMENTE as colunas definidas, ignora 'dia', 'semana' e outras extras"""
    df = df.copy()
    colunas_manter = []
    for col in df.columns:
        col_limpo = str(col).strip().lower()
        if col_limpo in [c.lower() for c in COLUNAS_OFICIAIS] or col == "rowid":
            colunas_manter.append(col)
        # Ignora explicitamente
        elif col_limpo in ["dia", "semana", "mês", "ano", "semana do ano"]:
            continue
        else:
            colunas_manter.append(col)
    return df[colunas_manter]

def find_column(df, terms):
    for term in terms:
        term = term.lower().strip()
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if term in col_lower:
                return col
    return None

def ensure_column(df, column_name, default=""):
    if column_name not in df.columns:
        df[column_name] = default
    return column_name

def parse_date_series(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    result = pd.to_datetime(series, errors="coerce", dayfirst=True)
    mask = result.isna()
    if mask.any():
        result.loc[mask] = pd.to_datetime(
            series.loc[mask].astype(str).str.replace(".", "/", regex=False),
            errors="coerce",
            dayfirst=True,
        )
    return result

def safe_identifier(name):
    name = str(name)
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ ")
    if not name or any(ch not in allowed for ch in name):
        raise ValueError(f"Nome de coluna inválido: {name}")
    return '"' + name.replace('"', '""') + '"'

def parse_valor_numerico(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return 0
    s = str(valor).strip().replace("R$", "").replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return 0

# ============================================================
# MAPEAMENTO DAS COLUNAS
# ============================================================
def prepare_dataframe(df):
    df = normalize_columns(df)
    df = filtrar_colunas_oficiais(df)  # ✅ REMOVE extras

    col_obs = find_column(df, ["observaçao", "observacao", "observações", "informacoes"])
    col_acao = find_column(df, ["ação", "acao"])
    col_colab = find_column(df, ["colaborador", "colcaborador"])
    col_apq = find_column(df, ["apq"])

    col_obs = ensure_column(df, col_obs or "observações", "")
    col_acao = ensure_column(df, col_acao or "ação", "")
    col_colab = ensure_column(df, col_colab or "colaborador", "")
    col_apq = ensure_column(df, col_apq or "apq", "Pendente")

    df[col_apq] = (
        df[col_apq]
        .fillna("Pendente")
        .astype(str)
        .apply(
            lambda x: "Concluída"
            if x.strip().lower()
            in {"concluída", "concluida", "concluido", "sim", "1", "true"}
            else "Pendente"
        )
    )

    return df, {
        "secao": find_column(df, ["seção", "secao"]),
        "defeito": find_column(df, ["defeito"]),
        "nota": find_column(df, ["nota"]),
        "data": find_column(df, ["data"]),
        "turno": find_column(df, ["turno"]),
        "material": find_column(df, ["material"]),
        "desc_mat": find_column(df, ["descrição do material", "descricao do material"]),
        "ct": find_column(df, ["ct causador", "ct"]),
        "qtd": find_column(df, ["quantidade"]),
        "desc_feito": find_column(df, ["descrição do defeito", "descricao do defeito"]),
        "causa": find_column(df, ["causa"]),
        "texto_causa": find_column(df, ["texto da causa"]),
        "custo": find_column(df, ["custo"]),
        "obs": col_obs,
        "acao": col_acao,
        "colab": col_colab,
        "prep": find_column(df, ["preparador"]),
        "apq": col_apq,
        "twtp": find_column(df, ["twtp", "twttp"]),
    }

# ============================================================
# IMPORTAÇÃO DE ARQUIVO
# ============================================================
def import_excel(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".xls":
        return pd.read_excel(uploaded_file, sheet_name="Notas")
    return pd.read_excel(uploaded_file, sheet_name="Notas", engine="openpyxl")

# ============================================================
# 💾 SALVAR — FILTRA COLUNAS EXTRAS
# ============================================================
def save_imported_dataframe(df_novo):
    conn = get_connection()
    df_novo = filtrar_colunas_oficiais(df_novo)  # ✅ LIMPA colunas extras
    col_nota_novo = find_column(df_novo, ["nota"])

    if not col_nota_novo:
        raise ValueError("Coluna 'Nota' não encontrada no arquivo.")

    df_novo[col_nota_novo] = df_novo[col_nota_novo].astype(str).str.strip()
    notas_novas = set(df_novo[col_nota_novo].unique())

    linhas_novas = 0
    linhas_atualizadas = 0
    linhas_excluidas = 0
    notas_sumiram = []

    if table_exists():
        df_antigo = pd.read_sql(f'SELECT * FROM "{TABLE_NAME}"', conn)
        df_antigo = filtrar_colunas_oficiais(df_antigo)  # ✅ LIMPA colunas antigas
        col_nota_antigo = find_column(df_antigo, ["nota"])

        if col_nota_antigo:
            df_antigo[col_nota_antigo] = df_antigo[col_nota_antigo].astype(str).str.strip()
            notas_antigas = set(df_antigo[col_nota_antigo].unique())

            notas_sumiram = sorted(notas_antigas - notas_novas)
            linhas_excluidas = len(notas_sumiram)

            for _, linha in df_novo.iterrows():
                nota = linha[col_nota_novo]
                if nota in df_antigo[col_nota_antigo].values:
                    linhas_atualizadas += 1
                else:
                    linhas_novas += 1

            df_final = pd.concat([df_novo, df_antigo]).drop_duplicates(
                subset=col_nota_novo, keep="first"
            )
        else:
            df_final = df_novo
            linhas_novas = len(df_novo)
    else:
        df_final = df_novo
        linhas_novas = len(df_novo)

    df_final.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    return linhas_novas, linhas_atualizadas, linhas_excluidas, notas_sumiram

# ============================================================
# 📂 MENU LATERAL
# ============================================================
with st.sidebar:
    st.header("🛠️ Menu de Opções")
    with st.expander("📂 Importar e Gerenciar Dados", expanded=False):
        uploaded_file = st.file_uploader(
            "Enviar Planilha (.xlsx, .xlsm, .xls)",
            type=["xlsx", "xls", "xlsm"],
        )
        if uploaded_file is not None:
            if st.button("📥 Importar Aba 'Notas'", type="primary"):
                try:
                    df_novo = import_excel(uploaded_file)
                    if df_novo.empty:
                        st.warning("⚠️ A aba 'Notas' está vazia.")
                    else:
                        df_novo = normalize_columns(df_novo)
                        novas, atualizadas, excluidas, lista_excluir = save_imported_dataframe(df_novo)

                        st.success(f"✅ Importação concluída!")
                        st.info(f"🆕 Notas novas: {novas}  |  🔄 Atualizadas: {atualizadas}")

                        if excluidas > 0:
                            st.warning(
                                f"⚠️ {excluidas} Nota(s) NÃO estão no arquivo novo:\n" +
                                "\n".join([f"• {n}" for n in lista_excluir[:10]]) +
                                ("\n... e mais" if excluidas > 10 else "") +
                                "\n\nℹ️ Mantidas no banco. Exclua manualmente se necessário."
                            )
                        st.rerun()
                except ImportError:
                    st.error("Para arquivos .xls antigos, instale: pip install xlrd")
                except ValueError as e:
                    st.error(f"Erro na planilha: {e}")
                except Exception as e:
                    st.error(f"Erro ao importar: {e}")

    with st.expander("📄 Gerar Relatórios", expanded=False):
        st.info("Módulo de relatórios em desenvolvimento.")
        st.button("Gerar PDF com Gráficos", disabled=True)
        st.button("Gerar PDF para Reunião", disabled=True)

    st.divider()
    st.subheader("🔍 Filtros de Análise")

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================
df = load_data()
if df.empty:
    st.warning(
        "⚠️ O banco de dados está vazio. Abra o menu no canto superior direito → "
        "'📂 Importar e Gerenciar Dados' → envie sua planilha (aba 'Notas')."
    )
    st.stop()

df, cols = prepare_dataframe(df)

col_nota = cols["nota"]
col_data = cols["data"]
col_secao = cols["secao"]
col_turno = cols["turno"]
col_qtd = cols["qtd"]
col_custo = cols["custo"]
col_colab = cols["colab"]
col_obs = cols["obs"]
col_acao = cols["acao"]
col_apq = cols["apq"]

# ============================================================
# TRATAMENTO DE DATA
# ============================================================
if col_data:
    df[col_data] = parse_date_series(df[col_data])
    df["__ano__"] = df[col_data].dt.year.astype("Int64")
    df["__mes__"] = df[col_data].dt.month.astype("Int64")

# ============================================================
# FILTROS
# ============================================================
with st.sidebar:
    pesquisa_nota = st.text_input("Pesquisar Nota:")

    secoes = ["Todas"] + sorted(df[col_secao].dropna().astype(str).str.strip().unique().tolist()) if col_secao else ["Todas"]
    filtro_secao = st.selectbox("Seção", secoes)

    turnos = ["Todos"] + sorted(df[col_turno].dropna().astype(str).str.strip().unique().tolist()) if col_turno else ["Todos"]
    filtro_turno = st.selectbox("Turno", turnos)

    filtro_mes, filtro_ano = "Todos", "Todos"
    if col_data and not df["__mes__"].dropna().empty:
        meses = ["Todos"] + sorted([str(int(x)) for x in df["__mes__"].dropna().unique()])
        filtro_mes = st.selectbox("Mês", meses)
        anos = ["Todos"] + sorted([str(int(x)) for x in df["__ano__"].dropna().unique()])
        filtro_ano = st.selectbox("Ano", anos)

    colaboradores = ["Todos"] + sorted(df[col_colab].dropna().astype(str).str.strip().unique().tolist()) if col_colab else ["Todos"]
    filtro_colab = st.selectbox("Colaborador", colaboradores)

    data_ini, data_fim = None, None
    if col_data and not df[col_data].dropna().empty:
        min_d = df[col_data].min().date()
        max_d = df[col_data].max().date()
        data_ini = st.date_input("Data Inicial", value=min_d, min_value=min_d, max_value=max_d)
        data_fim = st.date_input("Data Final", value=max_d, min_value=min_d, max_value=max_d)
        if data_ini > data_fim:
            st.error("Data Inicial não pode ser maior que a Data Final.")

# ============================================================
# APLICA FILTROS
# ============================================================
df_filtrado = df.copy()

if pesquisa_nota and col_nota:
    df_filtrado = df_filtrado[df_filtrado[col_nota].astype(str).str.contains(pesquisa_nota, case=False, na=False)]
if filtro_secao != "Todas" and col_secao:
    df_filtrado = df_filtrado[df_filtrado[col_secao].astype(str).str.strip() == filtro_secao]
if filtro_turno != "Todos" and col_turno:
    df_filtrado = df_filtrado[df_filtrado[col_turno].astype(str).str.strip() == filtro_turno]
if filtro_mes != "Todos" and "__mes__" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["__mes__"].astype(str) == filtro_mes]
if filtro_ano != "Todos" and "__ano__" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["__ano__"].astype(str) == filtro_ano]
if filtro_colab != "Todos" and col_colab:
    df_filtrado = df_filtrado[df_filtrado[col_colab].astype(str).str.strip() == filtro_colab]
if col_data and data_ini and data_fim and data_ini <= data_fim:
    df_filtrado = df_filtrado[
        (df_filtrado[col_data].dt.date >= data_ini) &
        (df_filtrado[col_data].dt.date <= data_fim)
    ]

# ============================================================
# 📊 INDICADORES
# ============================================================
st.subheader(f"📊 Registros Encontrados — {len(df_filtrado):,}")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("📋 Total de Notas", f"{df_filtrado[col_nota].nunique(dropna=True):,}" if col_nota else "N/D")

with c2:
    if col_qtd:
        qtd_total = df_filtrado[col_qtd].apply(parse_valor_numerico).sum()
        st.metric("📦 Quantidade Refugada", f"{qtd_total:,.0f}")
    else:
        st.metric("📦 Quantidade", "N/D")

with c3:
    if col_custo:
        custo_total = df_filtrado[col_custo].apply(parse_valor_numerico).sum()
        st.metric("💰 Custo Total", f"R$ {custo_total:,.2f}")
    else:
        st.metric("💰 Custo Total", "N/D")

with c4:
    if col_apq:
        concluidas = df_filtrado[col_apq].astype(str).str.lower().eq("concluída").sum()
        pendentes = df_filtrado[col_apq].astype(str).str.lower().eq("pendente").sum()
        st.metric("✅ APQ Concluídas", f"{concluidas:,} / {concluidas + pendentes:,}")
    else:
        st.metric("✅ APQ Concluídas", "N/D")

# ============================================================
# ✏️ TABELA — SEM COLUNAS EXTRAS!
# ============================================================
st.markdown("💡 **Edição direta:** altere Observação, Ação, Colaborador e APQ → clique em **Salvar Alterações**.")

# ✅ EXCLUI colunas internas da visualização
cols_exibir = [c for c in df_filtrado.columns if c not in ["__ano__", "__mes__"]]
df_editar = df_filtrado[cols_exibir].copy()

df_salvo = st.data_editor(
    df_editar,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        col_apq: st.column_config.SelectboxColumn(
            "APQ (Status)",
            options=["Concluída", "Pendente"],
            required=True,
        )
    } if col_apq else {},
    key="tabela_editor",
)

# ============================================================
# 💾 SALVAR ALTERAÇÕES
# ============================================================
if st.button("💾 Salvar Alterações no Banco", type="primary"):
    try:
        if "rowid" not in df_salvo.columns:
            raise ValueError("Coluna 'rowid' não encontrada. Reimporte os dados.")

        conn = get_connection()
        for _, linha in df_salvo.iterrows():
            rid = int(linha["rowid"])
            obs_val = str(linha.get(col_obs, "")).strip()
            acao_val = str(linha.get(col_acao, "")).strip()
            colab_val = str(linha.get(col_colab, "")).strip()
            apq_val = str(linha.get(col_apq, "Pendente")).strip()

            conn.execute(f"""
                UPDATE {safe_identifier(TABLE_NAME)}
                SET {safe_identifier(col_obs)} = ?,
                    {safe_identifier(col_acao)} = ?,
                    {safe_identifier(col_colab)} = ?,
                    {safe_identifier(col_apq)} = ?
                WHERE rowid = ?
            """, (obs_val, acao_val, colab_val, apq_val, rid))

        conn.commit()
        conn.close()
        st.success("✅ Alterações salvas com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {e}")

# ============================================================
# ⚠️ LIMPEZA DO BANCO
# ============================================================
with st.sidebar:
    st.divider()
    st.subheader("⚠️ Administração")
    if st.button("🗑️ Limpar Banco de Dados"):
        if st.session_state.get("confirmar_limpar", False):
            conn = get_connection()
            conn.execute(f"DROP TABLE IF EXISTS {safe_identifier(TABLE_NAME)}")
            conn.commit()
            conn.close()
            st.session_state["confirmar_limpar"] = False
            st.success("✅ Banco de dados apagado. Reimporte sua planilha sem as colunas extras!")
            st.rerun()
        else:
            st.session_state["confirmar_limpar"] = True
            st.warning("⚠️ Clique NOVAMENTE para confirmar a exclusão TOTAL dos dados.")
