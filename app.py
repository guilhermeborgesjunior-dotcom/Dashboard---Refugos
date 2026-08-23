import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date
from io import BytesIO

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

# ✅ COLUNAS QUE QUEREMOS DA ABA "NOTAS" (nome: índice da coluna)
# Baseado na análise do seu arquivo:
# 3=SEÇÃO, 4=DEFEITO, 5=NOTA, 6=DATA, 7=TURNO, 10=MATERIAL
# 11=DESCRIÇÃO DO MATERIAL, 12=CT CAUSADOR, 13=QUANTIDADE
# 16=DESCRIÇÃO DO DEFEITO, 18=CAUSA, 19=TEXTO DA CAUSA, 21=CUSTO REFUGO
COLUNAS_IMPORTAR = {
    "SEÇÃO": 2,       # índice 0-based = coluna C
    "DEFEITO": 3,     # coluna D
    "NOTA": 4,        # coluna E
    "DATA": 5,        # coluna F
    "TURNO": 6,       # coluna G
    "MATERIAL": 9,    # coluna J
    "DESCRIÇÃO DO MATERIAL": 10,  # coluna K
    "CT CAUSADOR": 11,           # coluna L
    "QUANTIDADE": 12,            # coluna M
    "DESCRIÇÃO DO DEFEITO": 15,  # coluna P
    "CAUSA": 17,                 # coluna R
    "TEXTO DA CAUSA": 18,        # coluna S
    "CUSTO REFUGO": 20,          # coluna V
}

COLUNAS_IGNORAR = ["dia", "semana", "mês", "ano", "__ano__", "__mes__"]

# ============================================================
# ESTILO
# ============================================================
st.markdown("""
<style>
.block-container { padding-top: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
.header-container {
    background: linear-gradient(rgba(10,25,47,.88), rgba(10,25,47,.88)), url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1600&q=80');
    background-size: cover; background-position: center;
    padding: 35px 40px; border-radius: 0 0 12px 12px; color: white;
    margin: -4rem -2rem 1rem -2rem; box-shadow: 0 4px 6px rgba(0,0,0,.3);
}
.header-title { font-size: 2.2rem; font-weight: 700; margin: 0; color: #fff; }
.header-subtitle { font-size: 1rem; color: #94a3b8; margin-top: 5px; }
[data-testid="collapsedControl"] { position: fixed !important; top: 15px !important; right: 20px !important; z-index: 999999 !important; background-color: #0a192f !important; border-radius: 5px; color: white !important; }
</style>
<div class="header-container">
    <div class="header-title">⚙️ Dashboard de Refugos - WEG UFE</div>
    <div class="header-subtitle">Gestão de Apontamentos da Aba "Notas"</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# BANCO DE DADOS
# ============================================================
def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def table_exists():
    if not DB_PATH.exists(): return False
    conn = get_connection()
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,))
        return cur.fetchone() is not None
    finally: conn.close()

def converter_datas_para_texto(df):
    """Converte datas para string compatível com SQLite"""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d").fillna("")
    return df

def load_data():
    if not table_exists(): return pd.DataFrame()
    conn = get_connection()
    try:
        df = pd.read_sql(f'SELECT rowid, * FROM "{TABLE_NAME}"', conn)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()
    finally: conn.close()

# ============================================================
# UTILITÁRIOS
# ============================================================
def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().replace("\n", " ").title() for c in df.columns]
    return df

def find_column(df, terms):
    for t in terms:
        t = t.lower().strip()
        for c in df.columns:
            if t in str(c).lower().strip(): return c
    return None

def parse_date_series(series):
    result = pd.to_datetime(series, errors="coerce", dayfirst=True)
    mask = result.isna()
    if mask.any():
        result.loc[mask] = pd.to_datetime(
            series.loc[mask].astype(str).str.replace(".", "/", regex=False),
            errors="coerce", dayfirst=True
        )
    return result

def parse_valor_numerico(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0
    s = str(valor).strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try: return float(s)
    except: return 0

# ============================================================
# 🚀 LEITURA OTIMIZADA — DIRETO DA MEMÓRIA, SÓ COLUNAS NECESSÁRIAS
# ============================================================
def ler_arquivo_otimizado(arquivo_carregado):
    """
    Lê APENAS a aba "Notas" e SOMENTE as colunas que precisamos.
    Muito mais rápido! Usa openpyxl em modo leitura.
    """
    import openpyxl
    
    # Lê direto da memória (BytesIO), sem arquivo temporário
    dados_bytes = BytesIO(arquivo_carregado.getvalue())
    
    # Modo leitura + apenas valores (não recalcula fórmulas!)
    wb = openpyxl.load_workbook(dados_bytes, read_only=True, data_only=True)
    
    # Procura a aba "Notas"
    if "Notas" not in wb.sheetnames:
        raise ValueError(f"Aba 'Notas' não encontrada! Abas disponíveis: {', '.join(wb.sheetnames)}")
    
    ws = wb["Notas"]
    
    # Pega os índices das colunas que queremos
    indices_colunas = list(COLUNAS_IMPORTAR.values())
    nomes_colunas = list(COLUNAS_IMPORTAR.keys())
    
    # Lê os dados de forma eficiente (iter_rows)
    dados = []
    for i, linha in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i >= 10000: break  # limite de segurança
        
        # Verifica se a linha tem dados (pelo menos NOTA não vazia)
        if len(linha) <= 4 or linha[4] is None or str(linha[4]).strip() == "":
            continue
        
        registro = []
        for idx in indices_colunas:
            if idx < len(linha):
                valor = linha[idx]
                # Converte datas para string
                if isinstance(valor, datetime):
                    valor = valor.strftime("%Y-%m-%d")
                registro.append(valor)
            else:
                registro.append(None)
        dados.append(registro)
    
    wb.close()
    
    # Cria DataFrame
    df = pd.DataFrame(dados, columns=nomes_colunas)
    
    # Adiciona colunas extras para edição
    colunas_extras = ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP"]
    for col in colunas_extras:
        df[col] = ""
    
    # Define APQ padrão
    df["APQ"] = "Pendente"
    
    return df

# ============================================================
# 💾 SALVAR OTIMIZADO
# ============================================================
def salvar_dados(df_novo):
    df_novo = converter_datas_para_texto(df_novo)
    col_nota = find_column(df_novo, ["nota"])
    
    if not col_nota:
        raise ValueError("Coluna 'Nota' não encontrada!")

    df_novo[col_nota] = df_novo[col_nota].astype(str).str.strip()
    conn = get_connection()

    if table_exists():
        df_antigo = pd.read_sql(f'SELECT * FROM "{TABLE_NAME}"', conn)
        df_antigo = converter_datas_para_texto(df_antigo)
        col_nota_ant = find_column(df_antigo, ["nota"])
        
        if col_nota_ant:
            df_antigo[col_nota_ant] = df_antigo[col_nota_ant].astype(str).str.strip()
            notas_antigas = set(df_antigo[col_nota_ant].unique())
            novas = len(set(df_novo[col_nota].unique()) - notas_antigas)
            
            # Merge: mantém colunas extras (Observações, Ação, etc) dos dados antigos
            colunas_preservar = ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP", col_nota_ant]
            colunas_preservar = [c for c in colunas_preservar if c in df_antigo.columns]
            
            if len(colunas_preservar) > 1:
                df_antigo_preservar = df_antigo[colunas_preservar].copy()
                df_novo = df_novo.drop(columns=[c for c in colunas_preservar if c != col_nota], errors="ignore")
                df_novo = df_novo.merge(df_antigo_preservar, on=col_nota, how="left")
            
            df_final = pd.concat([df_novo, df_antigo]).drop_duplicates(subset=col_nota, keep="first")
        else:
            df_final = df_novo
            novas = len(df_novo)
    else:
        df_final = df_novo
        novas = len(df_novo)

    df_final = converter_datas_para_texto(df_final)
    df_final.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    return len(df_novo), novas

# ============================================================
# 📂 MENU LATERAL
# ============================================================
with st.sidebar:
    st.header("🛠️ Menu de Opções")
    with st.expander("📂 Importar Dados", expanded=False):
        arq = st.file_uploader(
            "Selecione sua Planilha (.xlsx, .xlsm, .xls)",
            type=["xlsx", "xlsm", "xls"]
        )

        if arq is not None:
            try:
                with st.spinner(f"📖 Lendo {arq.name}..."):
                    df = ler_arquivo_otimizado(arq)
                
                if df.empty:
                    st.warning("⚠️ Nenhum dado encontrado na aba 'Notas'.")
                else:
                    with st.spinner("💾 Salvando no banco..."):
                        total, novas = salvar_dados(df)
                    
                    st.success(f"✅ {total} registros! ({novas} novas notas)")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                import traceback
                with st.expander("🔍 Detalhes"):
                    st.code(traceback.format_exc())

    st.divider()
    st.subheader("🔍 Filtros")

# ============================================================
# CARREGAR DADOS
# ============================================================
df = load_data()
if df.empty:
    st.warning("⚠️ Banco vazio → Selecione sua planilha no menu lateral 👆")
    st.stop()

# Mapeia colunas
col_nota = find_column(df, ["nota"])
col_data = find_column(df, ["data"])
col_secao = find_column(df, ["seção", "secao"])
col_turno = find_column(df, ["turno"])
col_qtd = find_column(df, ["quantidade"])
col_custo = find_column(df, ["custo"])
col_colab = find_column(df, ["colaborador"])
col_obs = find_column(df, ["observação", "observacao", "observações"])
col_acao = find_column(df, ["ação", "acao"])
col_apq = find_column(df, ["apq"])

# Trata data
if col_data:
    df[col_data] = parse_date_series(df[col_data])
    df["__ano__"] = df[col_data].dt.year.astype("Int64")
    df["__mes__"] = df[col_data].dt.month.astype("Int64")

# ============================================================
# FILTROS
# ============================================================
with st.sidebar:
    pesq_nota = st.text_input("Pesquisar Nota")
    secoes = ["Todas"] + sorted(df[col_secao].dropna().astype(str).str.strip().unique().tolist()) if col_secao else ["Todas"]
    f_secao = st.selectbox("Seção", secoes)
    turnos = ["Todos"] + sorted(df[col_turno].dropna().astype(str).str.strip().unique().tolist()) if col_turno else ["Todos"]
    f_turno = st.selectbox("Turno", turnos)

    f_mes = f_ano = "Todos"
    if col_data and not df["__mes__"].dropna().empty:
        f_mes = st.selectbox("Mês", ["Todos"] + sorted([str(int(x)) for x in df["__mes__"].dropna().unique()]))
        f_ano = st.selectbox("Ano", ["Todos"] + sorted([str(int(x)) for x in df["__ano__"].dropna().unique()]))

# Aplica filtros
df_filt = df.copy()
if pesq_nota and col_nota:
    df_filt = df_filt[df_filt[col_nota].astype(str).str.contains(pesq_nota, case=False, na=False)]
if f_secao != "Todas" and col_secao:
    df_filt = df_filt[df_filt[col_secao].astype(str).str.strip() == f_secao]
if f_turno != "Todos" and col_turno:
    df_filt = df_filt[df_filt[col_turno].astype(str).str.strip() == f_turno]
if f_mes != "Todos" and "__mes__" in df_filt.columns:
    df_filt = df_filt[df_filt["__mes__"].astype(str) == f_mes]
if f_ano != "Todos" and "__ano__" in df_filt.columns:
    df_filt = df_filt[df_filt["__ano__"].astype(str) == f_ano]

# ============================================================
# INDICADORES
# ============================================================
st.subheader(f"📊 Registros: {len(df_filt):,}")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("📋 Notas Únicas", f"{df_filt[col_nota].nunique():,}" if col_nota else "N/D")
with c2: st.metric("📦 Quantidade", f"{df_filt[col_qtd].apply(parse_valor_numerico).sum():,.0f}" if col_qtd else "N/D")
with c3: st.metric("💰 Custo Total", f"R$ {df_filt[col_custo].apply(parse_valor_numerico).sum():,.2f}" if col_custo else "N/D")
with c4:
    if col_apq:
        conc = df_filt[col_apq].astype(str).str.lower().isin(["concluída", "concluida", "sim"]).sum()
        pend = len(df_filt) - conc
        st.metric("✅ APQ Concluídas", f"{conc} / {conc+pend}")
    else: st.metric("✅ APQ Concluídas", "N/D")

# ============================================================
# TABELA
# ============================================================
cols_exibir = [c for c in df_filt.columns if c not in ["__ano__", "__mes__"]]
df_edit = df_filt[cols_exibir].copy()

# Configura coluna APQ como select
config_colunas = {}
if col_apq:
    config_colunas[col_apq] = st.column_config.SelectboxColumn(
        "APQ", options=["Pendente", "Concluída"], required=True
    )

df_salvo = st.data_editor(
    df_edit, use_container_width=True, hide_index=True, num_rows="fixed",
    column_config=config_colunas, key="tabela_editor"
)

# Botão salvar
if st.button("💾 Salvar Alterações", type="primary"):
    try:
        if "rowid" not in df_salvo.columns:
            raise ValueError("Reimporte os dados.")
        
        conn = get_connection()
        for _, linha in df_salvo.iterrows():
            rid = int(linha["rowid"])
            obs = str(linha.get(col_obs, "")).strip() if col_obs else ""
            acao = str(linha.get(col_acao, "")).strip() if col_acao else ""
            colab = str(linha.get(col_colab, "")).strip() if col_colab else ""
            apq = str(linha.get(col_apq, "Pendente")).strip() if col_apq else "Pendente"
            
            conn.execute(f"""
                UPDATE "{TABLE_NAME}"
                SET "Observações"=?, "Ação"=?, "Colaborador"=?, "APQ"=?
                WHERE rowid=?
            """, (obs, acao, colab, apq, rid))
        
        conn.commit()
        conn.close()
        st.success("✅ Salvo!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro: {e}")
