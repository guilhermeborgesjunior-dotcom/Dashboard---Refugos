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
        return pd.read_sql(f'SELECT rowid, * FROM "{TABLE_NAME}"', conn)
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


def find_column(df, terms):
    for term in terms:
        term = term.lower()
        for col in df.columns:
            if term in str(col).lower():
                return col
    return None


def ensure_column(df, column_name, default=""):
    if column_name not in df.columns:
        df[column_name] = default
    return column_name


def parse_date_series(series):
    """
    Tenta interpretar datas vindas de Excel/SAP.
    Aceita datas reais, dd/mm/yyyy, dd.mm.yyyy e outros formatos
    reconhecidos pelo pandas.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    result = pd.to_datetime(series, errors="coerce", dayfirst=True)

    # Segunda tentativa para valores que possam ter vindo como string
    mask = result.isna()
    if mask.any():
        result.loc[mask] = pd.to_datetime(
            series.loc[mask].astype(str).str.replace(".", "/", regex=False),
            errors="coerce",
            dayfirst=True,
        )

    return result


def safe_identifier(name):
    """
    Valida identificadores SQL para impedir que nomes inesperados de
    colunas sejam inseridos diretamente no SQL.
    """
    name = str(name)
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ ")
    if not name or any(ch not in allowed for ch in name):
        raise ValueError(f"Nome de coluna inválido: {name}")
    return '"' + name.replace('"', '""') + '"'


def prepare_dataframe(df):
    df = normalize_columns(df)

    # Campos utilizados pelo Dashboard
    col_obs = find_column(df, ["observaçao", "observacao", "informacoes", "informações"])
    col_acao = find_column(df, ["ação", "acao"])
    col_colab = find_column(df, ["colaborador", "colcaborador"])
    col_apq = find_column(df, ["apq"])

    col_obs = ensure_column(df, col_obs or "observacao", "")
    col_acao = ensure_column(df, col_acao or "acao", "")
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
        "ct": find_column(df, ["ct causador"]),
        "qtd": find_column(df, ["quantidade"]),
        "desc_feito": find_column(
            df,
            [
                "descrição do feito",
                "descricao do feito",
                "descrição do defeito",
                "descricao do defeito",
            ],
        ),
        "causa": find_column(df, ["causa"]),
        "texto_causa": find_column(df, ["texto da causa"]),
        "custo": find_column(df, ["custo"]),
        "obs": col_obs,
        "acao": col_acao,
        "colab": col_colab,
        "prep": find_column(df, ["preparador"]),
        "apq": col_apq,
    }


def import_excel(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".xls":
        # xlrd é necessário para arquivos XLS antigos.
        return pd.read_excel(uploaded_file, sheet_name="Notas")

    return pd.read_excel(
        uploaded_file,
        sheet_name="Notas",
        engine="openpyxl",
    )


def save_imported_dataframe(df):
    conn = get_connection()
    try:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


# ============================================================
# MENU LATERAL
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
                        st.warning("A aba 'Notas' está vazia.")
                    else:
                        df_novo = normalize_columns(df_novo)
                        save_imported_dataframe(df_novo)
                        st.success(
                            f"✅ {len(df_novo):,} registros importados com sucesso."
                        )
                        st.rerun()

                except ImportError:
                    st.error(
                        "Para arquivos .xls antigos, instale o pacote 'xlrd'."
                    )
                except ValueError as e:
                    st.error(f"Erro na planilha: {e}")
                except Exception as e:
                    st.error(f"Erro ao importar a aba 'Notas': {e}")

    with st.expander("📄 Gerar Relatórios", expanded=False):
        st.info(
            "A estrutura está preparada para receber os módulos de PDF, "
            "gráficos e relatório executivo."
        )
        st.button("Gerar PDF com Gráficos", disabled=True)
        st.button("Gerar PDF para Reunião de Turno", disabled=True)

    st.divider()

    st.subheader("🔍 Filtros de Análise")


# ============================================================
# CARREGAMENTO
# ============================================================
df = load_data()

if df.empty:
    st.warning(
        "⚠️ O banco de dados está vazio. "
        "Abra o menu no canto superior direito, entre em "
        "'📂 Importar e Gerenciar Dados' e envie a planilha."
    )
    st.stop()

df, columns = prepare_dataframe(df)

col_secao = columns["secao"]
col_nota = columns["nota"]
col_data = columns["data"]
col_turno = columns["turno"]
col_colab = columns["colab"]
col_obs = columns["obs"]
col_acao = columns["acao"]
col_apq = columns["apq"]


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

    secoes = (
        ["Todas"]
        + sorted(
            df[col_secao].dropna().astype(str).str.strip().unique().tolist()
        )
        if col_secao
        else ["Todas"]
    )
    filtro_secao = st.selectbox("Seção", secoes)

    turnos = (
        ["Todos"]
        + sorted(
            df[col_turno].dropna().astype(str).str.strip().unique().tolist()
        )
        if col_turno
        else ["Todos"]
    )
    filtro_turno = st.selectbox("Turno", turnos)

    if col_data:
        meses = (
            ["Todos"]
            + [
                str(int(x))
                for x in sorted(df["__mes__"].dropna().unique())
            ]
        )
        filtro_mes = st.selectbox("Mês", meses)

        anos = (
            ["Todos"]
            + [
                str(int(x))
                for x in sorted(df["__ano__"].dropna().unique())
            ]
        )
        filtro_ano = st.selectbox("Ano", anos)
    else:
        filtro_mes = "Todos"
        filtro_ano = "Todos"

    colaboradores = (
        ["Todos"]
        + sorted(
            df[col_colab].dropna().astype(str).str.strip().unique().tolist()
        )
        if col_colab
        else ["Todos"]
    )
    filtro_colab = st.selectbox("Colaborador", colaboradores)

    if col_data and not df[col_data].dropna().empty:
        st.write("Período de Data:")

        min_d = df[col_data].min().date()
        max_d = df[col_data].max().date()

        data_ini = st.date_input(
            "Data Inicial",
            value=min_d,
            min_value=min_d,
            max_value=max_d,
        )

        data_fim = st.date_input(
            "Data Final",
            value=max_d,
            min_value=min_d,
            max_value=max_d,
        )

        if data_ini > data_fim:
            st.error("A Data Inicial não pode ser maior que a Data Final.")


# ============================================================
# APLICAÇÃO DOS FILTROS
# ============================================================
df_filtrado = df.copy()

if pesquisa_nota and col_nota:
    df_filtrado = df_filtrado[
        df_filtrado[col_nota]
        .astype(str)
        .str.contains(pesquisa_nota, case=False, na=False)
    ]

if filtro_secao != "Todas" and col_secao:
    df_filtrado = df_filtrado[
        df_filtrado[col_secao].astype(str).str.strip() == filtro_secao
    ]

if filtro_turno != "Todos" and col_turno:
    df_filtrado = df_filtrado[
        df_filtrado[col_turno].astype(str).str.strip() == filtro_turno
    ]

if filtro_mes != "Todos" and "__mes__" in df_filtrado.columns:
    df_filtrado = df_filtrado[
        df_filtrado["__mes__"].astype("Int64").astype(str) == filtro_mes
    ]

if filtro_ano != "Todos" and "__ano__" in df_filtrado.columns:
    df_filtrado = df_filtrado[
        df_filtrado["__ano__"].astype("Int64").astype(str) == filtro_ano
    ]

if filtro_colab != "Todos" and col_colab:
    df_filtrado = df_filtrado[
        df_filtrado[col_colab].astype(str).str.strip() == filtro_colab
    ]

if (
    col_data
    and "data_ini" in locals()
    and "data_fim" in locals()
    and data_ini <= data_fim
):
    df_filtrado = df_filtrado[
        (df_filtrado[col_data].dt.date >= data_ini)
        & (df_filtrado[col_data].dt.date <= data_fim)
    ]


# ============================================================
# INDICADORES RESUMIDOS
# ============================================================
st.subheader(f"📊 Registros Encontrados ({len(df_filtrado):,})")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Registros", f"{len(df_filtrado):,}")

with c2:
    if col_nota:
        st.metric(
            "Notas",
            f"{df_filtrado[col_nota].nunique(dropna=True):,}",
        )
    else:
        st.metric("Notas", "N/D")

with c3:
    if col_apq:
        concluidas = (
            df_filtrado[col_apq].astype(str).str.lower().eq("concluída").sum()
        )
        st.metric("APQ Concluídas", f"{concluidas:,}")
    else:
        st.metric("APQ Concluídas", "N/D")

with c4:
    if col_apq:
        pendentes = (
            df_filtrado[col_apq].astype(str).str.lower().eq("pendente").sum()
        )
        st.metric("APQ Pendentes", f"{pendentes:,}")
    else:
        st.metric("APQ Pendentes", "N/D")


# ============================================================
# TABELA EDITÁVEL
# ============================================================
st.markdown(
    "💡 **Edição:** altere diretamente **Observação**, **Ação**, "
    "**Colaborador** e **APQ**. Depois clique em **Salvar Alterações**."
)

cols_para_exibir = [
    c for c in df_filtrado.columns
    if c not in ["__ano__", "__mes__"]
]

df_para_editar = df_filtrado[cols_para_exibir].copy()

df_editado = st.data_editor(
    df_para_editar,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        col_apq: st.column_config.SelectboxColumn(
            "APQ (Status)",
            help="Selecione o status de conclusão",
            options=["Concluída", "Pendente"],
            required=True,
        )
    },
    key="editor_tabela_refugos",
)


# ============================================================
# SALVAR ALTERAÇÕES
# ============================================================
if st.button("💾 Salvar Alterações no Banco", type="primary"):
    try:
        if "rowid" not in df_editado.columns:
            raise ValueError("A coluna interna rowid não foi encontrada.")

        conn = get_connection()

        for _, row in df_editado.iterrows():
            row_id = int(row["rowid"])

            valores = (
                row.get(col_obs, ""),
                row.get(col_acao, ""),
                row.get(col_colab, ""),
                row.get(col_apq, "Pendente"),
                row_id,
            )

            sql = f"""
                UPDATE {safe_identifier(TABLE_NAME)}
                SET
                    {safe_identifier(col_obs)} = ?,
                    {safe_identifier(col_acao)} = ?,
                    {safe_identifier(col_colab)} = ?,
                    {safe_identifier(col_apq)} = ?
                WHERE rowid = ?
            """

            conn.execute(sql, valores)

        conn.commit()
        conn.close()

        st.success("✅ Alterações salvas no banco de dados com sucesso!")
        st.rerun()

    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass

        st.error(f"❌ Erro ao salvar alterações: {e}")


# ============================================================
# LIMPEZA DO BANCO
# ============================================================
st.divider()

with st.sidebar:
    st.subheader("⚠️ Administração")

    if st.button("🗑️ Limpar Banco de Dados"):
        st.warning(
            "Esta operação apagará todos os registros da tabela importada."
        )

        if st.session_state.get("confirmar_limpeza", False):
            conn = get_connection()
            try:
                conn.execute(f"DROP TABLE IF EXISTS {safe_identifier(TABLE_NAME)}")
                conn.commit()
            finally:
                conn.close()

            st.session_state["confirmar_limpeza"] = False
            st.success("Banco de dados limpo.")
            st.rerun()
        else:
            st.session_state["confirmar_limpeza"] = True
            st.rerun()

    if st.session_state.get("confirmar_limpeza", False):
        st.error("⚠️ Clique novamente para confirmar a limpeza definitiva.")
