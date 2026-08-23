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

# ✅ COLUNAS DA ABA "NOTAS" (índice 0-based)
COLUNAS_IMPORTAR = {
    "SEÇÃO": 2,
    "DEFEITO": 3,
    "NOTA": 4,
    "DATA": 5,
    "TURNO": 6,
    "MATERIAL": 9,
    "DESCRIÇÃO DO MATERIAL": 10,
    "CT CAUSADOR": 11,
    "QUANTIDADE": 12,
    "DESCRIÇÃO DO DEFEITO": 15,
    "CAUSA": 17,
    "TEXTO DA CAUSA": 18,
    "CUSTO REFUGO": 20,
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

def load_data():
    if not table_exists(): return pd.DataFrame()
    conn = get_connection()
    try:
        return pd.read_sql(f'SELECT rowid, * FROM "{TABLE_NAME}"', conn)
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()
    finally: conn.close()

# ============================================================
# UTILITÁRIOS
# ============================================================
def find_column(df, terms):
    for t in terms:
        t = t.lower().strip()
        for c in df.columns:
            if t in str(c).lower().strip(): return c
    return None

def limpar_nota(valor):
    """✅ Converte nota para número inteiro, remove .0 e pontos de milhar"""
    if pd.isna(valor): return ""
    s = str(valor).strip()
    # Remove .0 no final
    s = re.sub(r'\.0+$', '', s)
    # Remove pontos de milhar
    s = s.replace('.', '').replace(',', '')
    # Remove caracteres não numéricos
    s = re.sub(r'[^0-9]', '', s)
    return s if s else ""

def formatar_data_br(valor):
    """✅ Converte data para formato dd/mm/aaaa"""
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    
    s = str(valor).strip()
    
    # Tenta vários formatos
    formatos = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
        "%d-%m-%Y", "%d.%m.%Y",
    ]
    
    for fmt in formatos:
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except:
            continue
    
    # Tenta com pandas
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%d/%m/%Y")
    except:
        pass
    
    return s

def parse_data_para_filtro(series):
    """Converte string dd/mm/aaaa para datetime (para filtros)"""
    return pd.to_datetime(series, format="%d/%m/%Y", errors="coerce", dayfirst=True)

def parse_valor_numerico(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0
    s = str(valor).strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try: return float(s)
    except: return 0

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
    indices_colunas = list(COLUNAS_IMPORTAR.values())
    nomes_colunas = list(COLUNAS_IMPORTAR.keys())
    
    dados = []
    for i, linha in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i >= 15000: break
        
        # Verifica se NOTA existe
        if len(linha) <= 4 or linha[4] is None or str(linha[4]).strip() == "":
            continue
        
        registro = []
        for idx in indices_colunas:
            if idx < len(linha):
                valor = linha[idx]
                
                # ✅ NOTA: limpar e converter para inteiro
                if idx == 4:  # coluna NOTA
                    valor = limpar_nota(valor)
                
                # ✅ DATA: converter para dd/mm/aaaa
                elif idx == 5:  # coluna DATA
                    valor = formatar_data_br(valor)
                
                # Outras datas
                elif isinstance(valor, datetime):
                    valor = valor.strftime("%d/%m/%Y")
                
                registro.append(valor)
            else:
                registro.append(None)
        dados.append(registro)
    
    wb.close()
    
    df = pd.DataFrame(dados, columns=nomes_colunas)
    
    # ✅ REMOVER DUPLICATAS pela coluna NOTA
    df = df.drop_duplicates(subset=["NOTA"], keep="first")
    
    # Adiciona colunas extras
    for col in ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP"]:
        df[col] = ""
    df["APQ"] = "Pendente"
    
    return df

# ============================================================
# 💾 SALVAR
# ============================================================
def salvar_dados(df_novo):
    col_nota = find_column(df_novo, ["nota"])
    if not col_nota:
        raise ValueError("Coluna 'Nota' não encontrada!")

    df_novo[col_nota] = df_novo[col_nota].astype(str).str.strip()
    
    # ✅ Remove duplicatas do novo arquivo
    df_novo = df_novo.drop_duplicates(subset=[col_nota], keep="first")
    
    conn = get_connection()

    if table_exists():
        df_antigo = pd.read_sql(f'SELECT * FROM "{TABLE_NAME}"', conn)
        col_nota_ant = find_column(df_antigo, ["nota"])
        
        if col_nota_ant:
            df_antigo[col_nota_ant] = df_antigo[col_nota_ant].astype(str).str.strip()
            
            # Preserva colunas de edição
            colunas_preservar = [c for c in 
                ["Observações", "Ação", "Colaborador", "Preparador", "APQ", "TWTP", col_nota_ant]
                if c in df_antigo.columns]
            
            if len(colunas_preservar) > 1:
                df_preservar = df_antigo[colunas_preservar].copy()
                colunas_remover = [c for c in colunas_preservar if c != col_nota]
                df_novo = df_novo.drop(columns=colunas_remover, errors="ignore")
                df_novo = df_novo.merge(df_preservar, on=col_nota, how="left")
            
            # ✅ Remove duplicatas no merge final
            df_final = pd.concat([df_novo, df_antigo]).drop_duplicates(subset=col_nota, keep="first")
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
                    st.warning("⚠️ Nenhum dado encontrado.")
                else:
                    with st.spinner("💾 Salvando..."):
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

# Converte data para filtro
df["__data_dt__"] = parse_data_para_filtro(df[col_data]) if col_data else pd.NaT
df["__ano__"] = df["__data_dt__"].dt.year.astype("Int64")
df["__mes__"] = df["__data_dt__"].dt.month.astype("Int64")

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
    if not df["__mes__"].dropna().empty:
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
if f_mes != "Todos":
    df_filt = df_filt[df_filt["__mes__"].astype(str) == f_mes]
if f_ano != "Todos":
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
cols_exibir = [c for c in df_filt.columns if c not in ["__data_dt__", "__ano__", "__mes__"]]
df_edit = df_filt[cols_exibir].copy()

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
