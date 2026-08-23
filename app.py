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
st.set_page_config(page_title="Dashboard de Refugos", layout="wide")

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
