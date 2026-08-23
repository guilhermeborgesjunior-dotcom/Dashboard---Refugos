import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date
from io import BytesIO
import re

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

COLUNAS_IMPORTAR = {
    "SEÇÃO": 2, "DEFEITO": 3, "NOTA": 4, "DATA": 5, "TURNO": 6,
    "MATERIAL": 9, "DESCRIÇÃO DO MATERIAL": 10, "CT CAUSADOR": 11,
    "QUANTIDADE": 12, "DESCRIÇÃO DO DEFEITO": 15, "CAUSA": 17,
    "TEXTO DA CAUSA": 18, "CUSTO REFUGO": 20,
}

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
# 🔧 FUNÇÕES DE LIMPEZA E CONVERSÃO
# ============================================================
def limpar_nota(valor):
    if pd.isna(valor): return ""
    s = str(valor).strip()
    s = re.sub(r'\.0+$', '', s)
    s = re.sub(r'\.\d+$', '', s)
    s = s.replace('.', '').replace(',', '')
    s = re.sub(r'[^0-9]', '', s)
    return s

def limpar_coluna_nota(df, col_nota):
    if col_nota and col_nota in df.columns:
        df[col_nota] = df[col_nota].apply(limpar_nota)
    return df

def formatar_data_br(valor):
    if pd.isna(valor) or str(valor).strip() == "": return ""
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d/%m/%Y")
    s = str(valor).strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y"]:
        try: return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except: continue
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(dt): return dt.strftime("%d/%m/%Y")
    except: pass
    return s

def converter_quantidade_inteira(valor):
    """✅ Converte quantidade para NÚMERO INTEIRO"""
    if pd.isna(valor) or str(valor).strip() == "":
        return 0
    s = str(valor).strip()
    # Remove pontos de milhar e troca vírgula decimal por ponto
    s = s.replace(".", "").replace(",", ".")
    try:
        return int(round(float(s)))
    except:
        return 0

def converter_custo(valor):
    """✅ Converte custo para valor monetário"""
    if pd.isna(valor) or str(valor).strip() == "":
        return 0.0
    s = str(valor).strip().replace("R$", "").replace(" ", "")
    # Se tem vírgula E ponto: ponto é milhar, vírgula é decimal
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    # Se só tem vírgula: é decimal
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0

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

def find_column(df, terms):
    for t in terms:
        t = t.lower().strip()
        for c in df.columns:
            if t in str(c).lower().strip(): return c
    return None

def load_data():
    if not table_exists(): return pd.DataFrame()
    conn = get_connection()
    try:
        df = pd.read_sql(f'SELECT rowid, * FROM "{TABLE_NAME}"', conn)
        col_nota = find_column(df, ["nota"])
        df = limpar_coluna_nota(df, col_nota)
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()
    finally: conn.close()

# ============================================================
# 🚀 LEITURA OTIMIZADA
# ============================================================
def ler_arquivo_otimizado(arquivo_carregado):
    import openpyxl
    dados_bytes = BytesIO(arquivo_carregado.getvalue())
    wb = openpyxl.load_workbook(dados_bytes, read_only=True, data_only=True)
    
    if "Notas" not in wb.sheetnames:
        raise ValueError(f"Aba 'Notas' não encontrada! Abas: {', '.join(wb.sheetnames)}")
    
    ws = wb["Notas"]
    indices = list(COLUNAS_IMPORTAR.values())
    nomes = list(COLUNAS_IMPORTAR.keys())
    idx_nota = nomes.index("NOTA")
    idx_data = nomes.index("DATA")
    idx_qtd = nomes.index("QUANTIDADE")
    
    dados = []
    for i, linha in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i >= 15000: break
        if len(linha) <= 4 or linha[4] is None or str(linha[4]).strip() == "":
            continue
        
        registro = []
        for j, idx in enumerate(indices):
            if idx < len(linha):
                valor = linha[idx]
                if j == idx_nota:
                    valor = limpar_nota(valor)
                elif j == idx_data:
                    valor = formatar_data_br(valor)
                elif j == idx_qtd:
                    valor = converter_quantidade_inteira(valor)  # ✅ Quantidade inteira
                elif isinstance(valor, datetime):
                    valor = valor.strftime("%d/%m/%Y")
                registro.append(valor)
            else:
                registro.append(None)
        dados.append(registro)
    
    wb.close()
    df = pd.DataFrame(dados, columns=nomes)
    
    # Remove duplicatas
    df = df.drop_duplicates(subset=["NOTA"], keep="first")
    
    # Colunas extras
    for col in ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP"]:
        df[col] = ""
    df["APQ"] = "Pendente"
    
    return df

# ============================================================
# 💾 SALVAR
# ============================================================
def salvar_dados(df_novo):
    col_nota = find_column(df_novo, ["nota"])
    if not col_nota: raise ValueError("Coluna 'Nota' não encontrada!")
    
    df_novo = limpar_coluna_nota(df_novo, col_nota)
    df_novo = df_novo.drop_duplicates(subset=[col_nota], keep="first")
    
    conn = get_connection()
    
    if table_exists():
        df_antigo = pd.read_sql(f'SELECT * FROM "{TABLE_NAME}"', conn)
        col_nota_ant = find_column(df_antigo, ["nota"])
        
        if col_nota_ant:
            df_antigo = limpar_coluna_nota(df_antigo, col_nota_ant)
            
            cols_pres = [c for c in 
                ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP", col_nota_ant]
                if c in df_antigo.columns]
            
            if len(cols_pres) > 1:
                df_pres = df_antigo[cols_pres].copy()
                cols_remover = [c for c in cols_pres if c != col_nota]
                df_novo = df_novo.drop(columns=cols_remover, errors="ignore")
                df_novo = df_novo.merge(df_pres, on=col_nota, how="left")
            
            df_final = pd.concat([df_novo, df_antigo]).drop_duplicates(subset=col_nota, keep="first")
            df_final = limpar_coluna_nota(df_final, col_nota)
            novas = len(set(df_novo[col_nota].unique()) - set(df_antigo[col_nota_ant].unique()))
        else:
            df_final = df_novo
            novas = len(df_novo)
    else:
        df_final = df_novo
        novas = len(df_novo)
    
    df_final.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    return len(df_novo), novas

# ============================================================
# 📂 MENU LATERAL
# ============================================================
with st.sidebar:
    st.header("🛠️ Menu")
    with st.expander("📂 Importar", expanded=False):
        arq = st.file_uploader("Planilha (.xlsx, .xlsm, .xls)", type=["xlsx", "xlsm", "xls"])
        if arq is not None:
            try:
                with st.spinner(f"📖 Lendo..."):
                    df = ler_arquivo_otimizado(arq)
                if df.empty:
                    st.warning("⚠️ Sem dados.")
                else:
                    with st.spinner("💾 Salvando..."):
                        total, novas = salvar_dados(df)
                    st.success(f"✅ {total} registros! ({novas} novas)")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ {str(e)}")
    
    st.divider()
    st.subheader("⚠️ Administração")
    if st.button("🗑️ Limpar Banco"):
        if DB_PATH.exists():
            DB_PATH.unlink()
            st.success("✅ Banco apagado!")
            st.rerun()
    
    st.divider()
    st.subheader("🔍 Filtros")

# ============================================================
# CARREGAR DADOS
# ============================================================
df = load_data()
if df.empty:
    st.warning("⚠️ Banco vazio → Importe sua planilha 👆")
    st.stop()

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

# Data para filtro
df["__dt__"] = pd.to_datetime(df[col_data], format="%d/%m/%Y", errors="coerce") if col_data else pd.NaT
df["__ano__"] = df["__dt__"].dt.year.astype("Int64")
df["__mes__"] = df["__dt__"].dt.month.astype("Int64")

# ============================================================
# FILTROS
# ============================================================
with st.sidebar:
    pesq = st.text_input("Pesquisar Nota")
    secoes = ["Todas"] + sorted(df[col_secao].dropna().astype(str).str.strip().unique().tolist()) if col_secao else ["Todas"]
    f_sec = st.selectbox("Seção", secoes)
    turnos = ["Todos"] + sorted(df[col_turno].dropna().astype(str).str.strip().unique().tolist()) if col_turno else ["Todos"]
    f_turno = st.selectbox("Turno", turnos)
    f_mes = f_ano = "Todos"
    if not df["__mes__"].dropna().empty:
        f_mes = st.selectbox("Mês", ["Todos"] + sorted([str(int(x)) for x in df["__mes__"].dropna().unique()]))
        f_ano = st.selectbox("Ano", ["Todos"] + sorted([str(int(x)) for x in df["__ano__"].dropna().unique()]))

# Aplica filtros
df_f = df.copy()
if pesq and col_nota:
    df_f = df_f[df_f[col_nota].astype(str).str.contains(pesq, case=False, na=False)]
if f_sec != "Todas" and col_secao:
    df_f = df_f[df_f[col_secao].astype(str).str.strip() == f_sec]
if f_turno != "Todos" and col_turno:
    df_f = df_f[df_f[col_turno].astype(str).str.strip() == f_turno]
if f_mes != "Todos":
    df_f = df_f[df_f["__mes__"].astype(str) == f_mes]
if f_ano != "Todos":
    df_f = df_f[df_f["__ano__"].astype(str) == f_ano]

# ============================================================
# 📊 CÁLCULO DOS INDICADORES
# ============================================================
st.subheader(f"📊 Registros: {len(df_f):,}")
c1, c2, c3, c4 = st.columns(4)

# ✅ 1. Total de Notas Únicas
with c1:
    total_notas = df_f[col_nota].nunique() if col_nota else 0
    st.metric("📋 Notas Únicas", f"{total_notas:,}")

# ✅ 2. Quantidade Total (INTEIRA)
with c2:
    if col_qtd:
        qtd_total = df_f[col_qtd].apply(converter_quantidade_inteira).sum()
        st.metric("📦 Quantidade", f"{int(qtd_total):,}")  # Inteiro
    else:
        st.metric("📦 Quantidade", "N/D")

# ✅ 3. Custo Total
with c3:
    if col_custo:
        custo_total = df_f[col_custo].apply(converter_custo).sum()
        st.metric("💰 Custo Total", f"R$ {custo_total:,.2f}")
    else:
        st.metric("💰 Custo Total", "N/D")

# ✅ 4. APQ Concluídas
with c4:
    if col_apq:
        concluidas = df_f[col_apq].astype(str).str.lower().isin(["concluída", "concluida", "sim"]).sum()
        st.metric("✅ APQ", f"{concluidas:,} / {len(df_f):,}")
    else:
        st.metric("✅ APQ", "N/D")

# ============================================================
# TABELA
# ============================================================
cols_exibir = [c for c in df_f.columns if c not in ["__dt__", "__ano__", "__mes__"]]
df_edit = df_f[cols_exibir].copy()

cfg = {}
if col_apq:
    cfg[col_apq] = st.column_config.SelectboxColumn("APQ", options=["Pendente", "Concluída"], required=True)
if col_qtd:
    cfg[col_qtd] = st.column_config.NumberColumn("QUANTIDADE", format="%d")  # ✅ Mostra como inteiro

df_salvo = st.data_editor(
    df_edit, use_container_width=True, hide_index=True, num_rows="fixed",
    column_config=cfg, key="tabela"
)

if st.button("💾 Salvar Alterações", type="primary"):
    try:
        if "rowid" not in df_salvo.columns: raise ValueError("Reimporte.")
        conn = get_connection()
        for _, linha in df_salvo.iterrows():
            rid = int(linha["rowid"])
            obs = str(linha.get(col_obs, "")).strip() if col_obs else ""
            acao = str(linha.get(col_acao, "")).strip() if col_acao else ""
            colab = str(linha.get(col_colab, "")).strip() if col_colab else ""
            apq = str(linha.get(col_apq, "Pendente")).strip() if col_apq else "Pendente"
            conn.execute(f'UPDATE "{TABLE_NAME}" SET "Observações"=?, "Ação"=?, "Colaborador"=?, "APQ"=? WHERE rowid=?',
                (obs, acao, colab, apq, rid))
        conn.commit(); conn.close()
        st.success("✅ Salvo!"); st.rerun()
    except Exception as e:
        st.error(f"❌ {e}")
