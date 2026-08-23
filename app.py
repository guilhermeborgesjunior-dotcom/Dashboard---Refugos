import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from supabase import create_client, Client
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# Configuração da Página e Tema Claro
# ---------------------------------------------------------
st.set_page_config(page_title="Control de Refugos — Qualidade", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Conexão Segura com o Supabase
# ---------------------------------------------------------
url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("SUPABASE_KEY")

if not url or not key:
    st.error("Chaves do Supabase não foram encontradas nos Secrets.")
    st.stop()

supabase: Client = create_client(url, key)

# ---------------------------------------------------------
# Função para Carregar Dados
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        response = supabase.table("refugos").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------
# Interface Principal
# ---------------------------------------------------------
st.title("🏭 Control de Refugos — Qualidade")

df_full = carregar_dados()

# Indicadores Rápidos
col1, col2 = st.columns(2)
with col1:
    st.caption("TOTAL DE REFUGOS")
    total_pcs = df_full["quantidade"].sum() if not df_full.empty and "quantidade" in df_full.columns else 0
    st.subheader(f"{total_pcs} pcs")

with col2:
    st.caption("VALOR TOTAL")
    total_valor = df_full["valor"].sum() if not df_full.empty and "valor" in df_full.columns else 0.0
    st.subheader(f"R$ {total_valor:,.2f}")

st.markdown("---")
st.subheader("Registros de Refugo")

if not df_full.empty:
    st.dataframe(df_full, use_container_width=True)
else:
    st.info("Nenhum registro encontrado no banco de dados.")
