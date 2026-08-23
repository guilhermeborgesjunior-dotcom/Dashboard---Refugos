import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date
from io import BytesIO
import re

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

COLUNAS_IMPORTAR = {
    "SEÇÃO": 2, "DEFEITO": 3, "NOTA": 4, "DATA": 5, "TURNO": 6,
    "MATERIAL": 9, "DESCRIÇÃO DO MATERIAL": 10, "CT CAUSADOR": 11,
    "QUANTIDADE": 12, "DESCRIÇÃO DO DEFEITO": 15, "CAUSA": 17,
    "TEXTO DA CAUSA": 18, "CUSTO REFUGO": 20,
}

# ============================================================
# 🎨 ESTILO PROFISSIONAL
# ============================================================
st.markdown("""
<style>
.block-container { padding: 1rem 2rem !important; max-width: 1
