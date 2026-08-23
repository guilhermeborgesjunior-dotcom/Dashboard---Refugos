import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date
import traceback
import numpy as np

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

# ✅ COLUNAS A IGNORAR
COLUNAS_IGNORAR = ["dia", "semana", "mês", "ano", "semana do ano", "__ano__", "__mes__"]

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

def remover_colunas_extras(df):
    cols = [c for c in df.columns if str(c).strip().lower() not in COLUNAS_IGNORAR]
    return df[cols]

def converter_datas_para_texto(df):
    """✅ Converte colunas Timestamp para string (compatível com SQLite)"""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d").fillna("")
        elif pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].astype(str).fillna("")
    return df

def load_data():
    if not table_exists(): return pd.DataFrame()
    conn = get_connection()
    try:
        df = pd.read_sql(f'SELECT rowid, * FROM "{TABLE_NAME}"', conn)
        return remover_colunas_extras(df)
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
        return pd.DataFrame()
    finally: conn.close()

# ============================================================
# UTILITÁRIOS
# ============================================================
def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().replace("\n", " ") for c in df.columns]
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
# 📂 LEITURA ROBUSTA DO ARQUIVO
# ============================================================
def ler_arquivo_excel(arquivo_carregado):
    nome_arquivo = arquivo_carregado.name
    sufixo = Path(nome_arquivo).suffix.lower()
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(arquivo_carregado.getvalue())
        caminho_temp = tmp.name
    
    try:
        # Tenta 1: openpyxl
        try:
            xl = pd.ExcelFile(caminho_temp, engine="openpyxl")
            abas = xl.sheet_names
            st.info(f"📑 Abas encontradas: {', '.join(abas)}")
            
            alvo = None
            for aba in abas:
                if "nota" in aba.lower():
                    alvo = aba
                    break
            
            if alvo is None:
                raise ValueError(f"Aba 'Notas' não encontrada!\nAbas disponíveis: {', '.join(abas)}")
            
            st.info(f"📖 Lendo aba: {alvo}")
            df = pd.read_excel(caminho_temp, sheet_name=alvo, engine="openpyxl")
            return df
            
        except Exception as e1:
            st.warning(f"Tentativa 1 falhou: {str(e1)[:100]}")
            
            # Tenta 2: xlrd
            if sufixo == ".xls":
                try:
                    xl = pd.ExcelFile(caminho_temp, engine="xlrd")
                    abas = xl.sheet_names
                    st.info(f"📑 Abas encontradas: {', '.join(abas)}")
                    
                    alvo = None
                    for aba in abas:
                        if "nota" in aba.lower():
                            alvo = aba
                            break
                    
                    if alvo:
                        st.info(f"📖 Lendo aba: {alvo}")
                        df = pd.read_excel(caminho_temp, sheet_name=alvo, engine="xlrd")
                        return df
                except Exception as e2:
                    st.warning(f"Tentativa 2 falhou: {str(e2)[:100]}")
            
            # Tenta 3: primeira aba
            try:
                st.info("📖 Tentando ler a PRIMEIRA aba...")
                df = pd.read_excel(caminho_temp, sheet_name=0, engine="openpyxl")
                st.success("✅ Leitura da primeira aba bem-sucedida!")
                return df
            except Exception as e3:
                raise RuntimeError(
                    f"Não foi possível ler o arquivo.\n"
                    f"Erro: {str(e3)}\n"
                    f"Dica: Verifique se o arquivo não está protegido por senha."
                )
    finally:
        try: Path(caminho_temp).unlink()
        except: pass

# ============================================================
# 💾 SALVAR DADOS — ✅ CORRIGIDO: converte datas antes de salvar
# ============================================================
def salvar_dados(df_novo):
    df_novo = remover_colunas_extras(df_novo)
    df_novo = converter_datas_para_texto(df_novo)  # ✅ SOLUÇÃO DO ERRO!
    
    col_nota = find_column(df_novo, ["nota"])
    
    if not col_nota:
        st.error("Coluna 'Nota' não encontrada!")
        st.write("Colunas disponíveis:")
        st.write(list(df_novo.columns))
        raise ValueError("Coluna 'Nota' não encontrada na planilha")

    df_novo[col_nota] = df_novo[col_nota].astype(str).str.strip()
    conn = get_connection()

    if table_exists():
        df_antigo = pd.read_sql(f'SELECT * FROM "{TABLE_NAME}"', conn)
        df_antigo = remover_colunas_extras(df_antigo)
        df_antigo = converter_datas_para_texto(df_antigo)  # ✅ Converte datas antigas também
        
        col_nota_ant = find_column(df_antigo, ["nota"])
        if col_nota_ant:
            df_antigo[col_nota_ant] = df_antigo[col_nota_ant].astype(str).str.strip()
            notas_antigas = set(df_antigo[col_nota_ant].unique())
            novas = len(set(df_novo[col_nota].unique()) - notas_antigas)
            df_final = pd.concat([df_novo, df_antigo]).drop_duplicates(subset=col_nota, keep="first")
        else:
            df_final = df_novo
            novas = len(df_novo)
    else:
        df_final = df_novo
        novas = len(df_novo)

    # ✅ Garante que NÃO tem Timestamp antes de salvar
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
                st.info(f"📖 Processando: {arq.name}...")
                df = ler_arquivo_excel(arq)
                
                if df.empty:
                    st.warning("⚠️ A planilha está vazia.")
                else:
                    df = normalize_columns(df)
                    total, novas = salvar_dados(df)
                    st.success(f"✅ {total} registros importados! ({novas} novas notas)")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ ERRO: {str(e)}")
                with st.expander("🔍 Ver detalhes técnicos"):
                    st.code(traceback.format_exc())

    st.divider()
    st.subheader("🔍 Filtros")

# ============================================================
# CARREGAR DADOS
# ============================================================
df = load_data()
if df.empty:
    st.warning("⚠️ Banco vazio → Selecione sua planilha no menu lateral acima 👆")
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
st.data_editor(df_edit, use_container_width=True, hide_index=True, num_rows="fixed", key="tabela")
