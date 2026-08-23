import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date
from io import BytesIO
import re
import json

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================
st.set_page_config(
    page_title="Dashboard Refugos - WEG UFE",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("refugos_weg.db")
TABLE_NAME = "tabela_notas"
PREFS_FILE = Path(".preferencias_usuario.json")

COLUNAS_IMPORTAR = {
    "SEÇÃO": 2, "DEFEITO": 3, "NOTA": 4, "DATA": 5, "TURNO": 6,
    "MATERIAL": 9, "DESCRIÇÃO DO MATERIAL": 10, "CT CAUSADOR": 11,
    "QUANTIDADE": 12, "DESCRIÇÃO DO DEFEITO": 15, "CAUSA": 17,
    "TEXTO DA CAUSA": 18, "CUSTO REFUGO": 20,
}

# ============================================================
# 💾 SALVAR/CARREGAR PREFERÊNCIAS
# ============================================================
def carregar_preferencias():
    if PREFS_FILE.exists():
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def salvar_preferencias(pref):
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(pref, f, ensure_ascii=False, indent=2)
    except:
        pass

prefs = carregar_preferencias()

# ============================================================
# 🎨 ESTILO PROFISSIONAL
# ============================================================
st.markdown("""
<style>
.block-container { padding: 1rem 2rem !important; max-width: 100% !important; }
.header-container {
    background: linear-gradient(90deg, #0a192f 0%, #112240 100%);
    padding: 1.2rem 2rem;
    border-radius: 8px;
    color: white;
    margin: 0 0 1.5rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.header-title { font-size: 1.6rem; font-weight: 700; margin: 0; color: #fff; }
.header-subtitle { font-size: 0.95rem; color: #8892b0; margin-top: 0.25rem; }
.metric-card {
    background: #f8fafc;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    border-left: 4px solid;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.metric-card.notas { border-color: #3b82f6; }
.metric-card.qtd  { border-color: #10b981; }
.metric-card.custo { border-color: #f59e0b; }
.metric-card.apq   { border-color: #8b5cf6; }
.metric-value { font-size: 1.8rem; font-weight: 700; line-height: 1.2; }
.metric-label { font-size: 0.85rem; color: #64748b; }
div[data-testid="stDataFrame"] { border-radius: 8px; }
th { background: #f1f5f9 !important; color: #334155 !important; font-weight: 600 !important; }
tr:nth-child(even) { background: #f8fafc; }
section[data-testid="stSidebar"] { background: #f1f5f9; }
</style>

<div class="header-container">
    <h1 class="header-title">⚙️ Dashboard de Refugos — WEG UFE</h1>
    <p class="header-subtitle">Gestão de Apontamentos · Aba "Notas"</p>
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
    if pd.isna(valor) or str(valor).strip() == "": return 0
    s = str(valor).strip().replace(".", "").replace(",", ".")
    try: return int(round(float(s)))
    except: return 0

def converter_custo(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    s = str(valor).strip().replace("R$", "").replace(" ", "")
    if "." in s and "," in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

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
                if j == idx_nota: valor = limpar_nota(valor)
                elif j == idx_data: valor = formatar_data_br(valor)
                elif j == idx_qtd: valor = converter_quantidade_inteira(valor)
                elif isinstance(valor, datetime): valor = valor.strftime("%d/%m/%Y")
                registro.append(valor)
            else:
                registro.append(None)
        dados.append(registro)
    
    wb.close()
    df = pd.DataFrame(dados, columns=nomes)
    df = df.drop_duplicates(subset=["NOTA"], keep="first")
    
    for col in ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP"]:
        df[col] = ""
    df["APQ"] = "Pendente"
    return df

# ============================================================
# 💾 SALVAR DADOS
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
# 📂 BARRA LATERAL — SIMPLIFICADA
# ============================================================
with st.sidebar:
    st.header("📂 Importar Dados")
    arq = st.file_uploader("Selecione a Planilha", type=["xlsx", "xlsm", "xls"], label_visibility="collapsed")
    if arq is not None:
        try:
            with st.spinner("Lendo arquivo..."):
                df = ler_arquivo_otimizado(arq)
            if df.empty:
                st.warning("⚠️ Sem dados encontrados.")
            else:
                with st.spinner("Salvando..."):
                    total, novas = salvar_dados(df)
                st.success(f"✅ {total} registros! ({novas} novas notas)")
                st.rerun()
        except Exception as e:
            st.error(f"❌ {str(e)}")

    st.divider()
    st.header("👁️ Colunas Visíveis")
    
    df_temp = load_data()
    selecionadas = []
    
    if not df_temp.empty:
        todas_colunas = [c for c in df_temp.columns if not c.startswith("__")]
        colunas_visiveis_salvas = prefs.get("colunas_visiveis", todas_colunas)
        colunas_visiveis_salvas = [c for c in colunas_visiveis_salvas if c in todas_colunas]
        
        selecionadas = st.multiselect(
            "Escolha quais colunas ver:",
            options=todas_colunas,
            default=colunas_visiveis_salvas,
            key="seletor_colunas"
        )
        
        if selecionadas != colunas_visiveis_salvas:
            prefs["colunas_visiveis"] = selecionadas
            salvar_preferencias(prefs)
            st.toast("✅ Preferência salva!")
