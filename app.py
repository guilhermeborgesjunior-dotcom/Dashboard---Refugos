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
# Conexão com o Supabase
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "SUA_URL_SUPABASE")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "SUA_CHAVE_SUPABASE")

import os
import streamlit as st
from supabase import create_client, Client

# Busca das chaves nos Secrets do Streamlit de forma direta
url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("SUPABASE_KEY")

if not url or not key:
    st.error("Chaves do Supabase não foram encontradas nos Secrets.")
    st.stop()

supabase: Client = create_client(url, key)

supabase = init_supabase()

st.set_page_config(page_title="Dashboard de Refugos", layout="wide")

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
# Gerador de PDF
# ---------------------------------------------------------
def gerar_pdf(df, filtros_str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#0F172A'), fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748B'))
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#334155'))
    cell_head = ParagraphStyle('Head', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#0F172A'), fontName='Helvetica-Bold')

    elements.append(Paragraph("DASHBOARD DE REFUGOS — RELATÓRIO DE QUALIDADE", title_style))
    elements.append(Paragraph(f"Emitido em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))

    tot_qtd = df['quantidade'].astype(int).sum() if not df.empty else 0
    tot_val = df['valor'].astype(float).sum() if not df.empty else 0.0
    elements.append(Paragraph(f"<b>Filtros:</b> {filtros_str}<br/><b>Total Refugos:</b> {tot_qtd} pcs | <b>Custo Total:</b> R$ {tot_val:,.2f}", sub_style))
    elements.append(Spacer(1, 10))

    headers = ["SEC", "DEF", "NOTA", "DATA", "TURNO", "MATERIAL", "DESCRIÇÃO MATERIAL", "CT", "QTD", "DEFEITO", "OBSERVAÇÃO"]
    table_data = [[Paragraph(h, cell_head) for h in headers]]

    for _, row in df.iterrows():
        table_data.append([
            Paragraph(str(row.get('secao', '')), cell_style),
            Paragraph(str(row.get('defeito_tipo', '')), cell_style),
            Paragraph(str(row.get('nota', '')), cell_style),
            Paragraph(str(row.get('data', '')), cell_style),
            Paragraph(str(row.get('turno', '')), cell_style),
            Paragraph(str(row.get('material', '')), cell_style),
            Paragraph(str(row.get('descricao_material', ''))[:22], cell_style),
            Paragraph(str(row.get('ct', '')), cell_style),
            Paragraph(str(row.get('quantidade', '')), cell_style),
            Paragraph(str(row.get('descricao_defeito', ''))[:20], cell_style),
            Paragraph(str(row.get('observacao', ''))[:20], cell_style),
        ])

    t = Table(table_data, colWidths=[20, 28, 45, 40, 25, 45, 110, 35, 20, 100, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# Painel Principal
# ---------------------------------------------------------
st.sidebar.title("🔍 Filtros de Pesquisa")
df_full = carregar_dados()

secoes = ["Todas"] + sorted(list(df_full['secao'].dropna().astype(str).unique())) if not df_full.empty else ["Todas"]
secao_sel = st.sidebar.selectbox("Seção", secoes)

turnos = ["Todos"] + sorted(list(df_full['turno'].dropna().astype(str).unique())) if not df_full.empty else ["Todos"]
turno_sel = st.sidebar.selectbox("Turno", turnos)

df_filtered = df_full.copy()
if not df_filtered.empty:
    if secao_sel != "Todas":
        df_filtered = df_filtered[df_filtered['secao'].astype(str) == secao_sel]
    if turno_sel != "Todos":
        df_filtered = df_filtered[df_filtered['turno'].astype(str) == turno_sel]

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Relatórios")
if st.sidebar.button("Gerar Relatório PDF"):
    pdf_bytes = gerar_pdf(df_filtered, f"Seção: {secao_sel} | Turno: {turno_sel}")
    st.sidebar.download_button(
        label="⬇️ Baixar PDF",
        data=pdf_bytes,
        file_name=f"relatorio_refugos_{datetime.date.today()}.pdf",
        mime="application/pdf"
    )

st.title("🏭 Control de Refugos — Qualidade")

tabs = st.tabs(["📊 Visão Geral & Observações", "📥 Importação Inteligente"])

# TAB 1: VISÃO GERAL E EDIÇÃO DE OBSERVAÇÕES
with tabs[0]:
    c1, c2 = st.columns(2)
    tot_refugos = df_filtered['quantidade'].astype(int).sum() if not df_filtered.empty else 0
    val_total = df_filtered['valor'].astype(float).sum() if not df_filtered.empty else 0.0

    c1.metric("TOTAL DE REFUGOS", f"{tot_refugos} pcs")
    c2.metric("VALOR TOTAL", f"R$ {val_total:,.2f}")

    st.subheader("Registros de Refugo")
    st.caption("Você pode alterar qualquer campo ou escrever **Observações** na coluna correspondente. Depois, clique no botão abaixo para salvar no banco.")

    if not df_filtered.empty:
        # Tabela editável diretamente na tela
        edited_df = st.data_editor(
            df_filtered,
            column_config={
                "observacao": st.column_config.TextColumn("Observações / Ação Corretiva", help="Insira anotações sobre este refugo", width="large"),
                "id": None # Oculta a coluna ID para não poluir
            },
            use_container_width=True,
            key="editor_refugos"
        )

        if st.button("💾 Salvar Observações e Alterações"):
            for _, row in edited_df.iterrows():
                supabase.table("refugos").update({
                    "secao": str(row['secao']),
                    "defeito_tipo": str(row['defeito_tipo']),
                    "data": str(row['data']),
                    "turno": str(row['turno']),
                    "material": str(row['material']),
                    "descricao_material": str(row['descricao_material']),
                    "ct": str(row['ct']),
                    "quantidade": int(row['quantidade']),
                    "descricao_defeito": str(row['descricao_defeito']),
                    "valor": float(row['valor']),
                    "observacao": str(row.get('observacao', ''))
                }).eq("id", row['id']).execute()

            st.success("Alterações e observações salvas permanentemente!")
            st.rerun()

# TAB 2: IMPORTAÇÃO INTELIGENTE (SEM DUPLICAR)
with tabs[1]:
    st.subheader("Importar Planilha Diária")
    st.info("💡 **Como funciona:** O sistema analisa a coluna 'NOTA'. Somente os registros que **ainda não existem no banco** serão adicionados. Nada antigo será apagado ou sobrescrito.")

    uploaded_file = st.file_uploader("Selecione a planilha do mês (Excel / CSV)", type=["xlsx", "csv"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
        else:
            df_upload = pd.read_excel(uploaded_file)

        # Padronização de nomes de colunas caso venham em caixa alta
        df_upload.columns = [c.lower().strip().replace(" ", "_") for c in df_upload.columns]

        # Mapeamento para nomes padrão caso necessário
        mapeamento = {
            "defeito": "defeito_tipo",
            "descrição_do_material": "descricao_material",
            "descrição_do_defeito": "descricao_defeito"
        }
        df_upload = df_upload.rename(columns=mapeamento)

        # Buscar NOTAS já existentes no Supabase
        notas_existentes = set(df_full['nota'].astype(str).tolist()) if not df_full.empty else set()

        # Filtrar apenas dados NOVOS
        df_novos = df_upload[~df_upload['nota'].astype(str).isin(notas_existentes)].copy()

        col_a, col_b = st.columns(2)
        col_a.metric("Total de linhas na planilha", len(df_upload))
        col_b.metric("Novos registros detectados", len(df_novos))

        if not df_novos.empty:
            st.write("Pré-visualização dos **novos dados** que serão inseridos:")
            st.dataframe(df_novos)

            if st.button("🚀 Confirmar e Importar Apenas Novos Dados"):
                # Garante que a coluna observacao exista nos novos
                if 'observacao' not in df_novos.columns:
                    df_novos['observacao'] = ''

                records = df_novos.to_dict(orient="records")
                supabase.table("refugos").insert(records).execute()

                st.success(f"{len(df_novos)} novos registros importados com sucesso!")
                st.rerun()
        else:
            st.warning("Nenhum dado novo encontrado nesta planilha. Todos os registros já estão salvos no banco de dados!")
