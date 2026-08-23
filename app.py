import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO
from supabase import create_client, Client
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# Configuração da Página e Tema Limpo / Clean UI
# ---------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Refugos | Qualidade & Produção",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Profissional Personalizada
st.markdown("""
    <style>
    /* Estilo Geral da Aplicação */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Cards de KPI Executivos */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.05);
        text-align: left;
    }
    .kpi-title {
        color: #64748B;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .kpi-value {
        color: #0F172A;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    .kpi-sub {
        color: #10B981;
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Modificações nos componentes nativos do Streamlit */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Conexão com o Supabase
# ---------------------------------------------------------
url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("SUPABASE_KEY")

if not url or not key:
    st.error("⚠️ Configuração pendente: Chaves do Supabase não encontradas nos Secrets.")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(url, key)

supabase: Client = init_supabase()

# ---------------------------------------------------------
# Funções de Dados (CRUD e Relatórios)
# ---------------------------------------------------------
@st.cache_data(ttl=30)
def carregar_dados():
    try:
        response = supabase.table("refugos").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            if "valor" in df.columns:
                df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
            if "quantidade" in df.columns:
                df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {e}")
        return pd.DataFrame()

def gerar_pdf(df_filtrado):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'), fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#64748B'))
    cell_head = ParagraphStyle('Head', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#FFFFFF'), fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#334155'))

    elements.append(Paragraph("Relatório Executivo de Refugos — Qualidade", title_style))
    elements.append(Paragraph(f"Emitido em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}", sub_style))
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=15))

    # Dados da Tabela Resumida
    table_data = [[
        Paragraph("Seção", cell_head),
        Paragraph("Turno", cell_head),
        Paragraph("Defeito", cell_head),
        Paragraph("Qtd", cell_head),
        Paragraph("Valor (R$)", cell_head)
    ]]

    for _, row in df_filtrado.iterrows():
        table_data.append([
            Paragraph(str(row.get("secao", "-")), cell_style),
            Paragraph(str(row.get("turno", "-")), cell_style),
            Paragraph(str(row.get("defeito_tipo", "-")), cell_style),
            Paragraph(str(row.get("quantidade", 0)), cell_style),
            Paragraph(f"R$ {float(row.get('valor', 0)):,.2f}", cell_style)
        ])

    t = Table(table_data, colWidths=[100, 70, 180, 60, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# Carregamento e Filtros na Sidebar
# ---------------------------------------------------------
df_raw = carregar_dados()

with st.sidebar:
    st.markdown("### 🔍 Filtros Estratégicos")
    
    if not df_raw.empty:
        secoes = ["Todas"] + sorted(list(df_raw["secao"].dropna().unique())) if "secao" in df_raw.columns else ["Todas"]
        turnos = ["Todos"] + sorted(list(df_raw["turno"].dropna().unique())) if "turno" in df_raw.columns else ["Todos"]
        
        secao_sel = st.selectbox("Seção / Setor", secoes)
        turno_sel = st.selectbox("Turno Operacional", turnos)
        
        # Aplicação dos Filtros
        df_filtered = df_raw.copy()
        if secao_sel != "Todas":
            df_filtered = df_filtered[df_filtered["secao"] == secao_sel]
        if turno_sel != "Todos":
            df_filtered = df_filtered[df_filtered["turno"] == turno_sel]
    else:
        df_filtered = pd.DataFrame()
        st.info("Nenhum dado cadastrado para filtragem.")

    st.markdown("---")
    st.markdown("### 📄 Relatórios")
    if not df_filtered.empty:
        pdf_file = gerar_pdf(df_filtered)
        st.download_button(
            label="📥 Exportar Relatório PDF",
            data=pdf_file,
            file_name=f"relatorio_refugos_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# ---------------------------------------------------------
# Painel Principal e Abas
# ---------------------------------------------------------
st.title("🏭 Control de Refugos — Gestão de Qualidade")
st.markdown("Painel analítico para monitoramento de perdas, custos de não-conformidade e análise operacional.")

tab1, tab2, tab3 = st.tabs(["📊 Visão Geral & Métricas", "➕ Novo Registro", "🗂️ Base de Dados"])

# ---------------------------------------------------------
# TAB 1: VISÃO GERAL
# ---------------------------------------------------------
with tab1:
    if not df_filtered.empty:
        # Métricas de KPI executivas
        tot_qtd = int(df_filtered["quantidade"].sum())
        tot_val = float(df_filtered["valor"].sum())
        ticket_medio = tot_val / tot_qtd if tot_qtd > 0 else 0
        total_registros = len(df_filtered)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Refugado</div><div class="kpi-value">{tot_qtd:,} <span style="font-size: 1rem;">pcs</span></div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Custo Total de Refugo</div><div class="kpi-value">R$ {tot_val:,.2f}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Custo Médio / Peça</div><div class="kpi-value">R$ {ticket_medio:,.2f}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Ocorrências</div><div class="kpi-value">{total_registros}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráficos de Análise
        g1, g2 = st.columns(2)
        
        with g1:
            if "defeito_tipo" in df_filtered.columns:
                df_def = df_filtered.groupby("defeito_tipo")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                fig_def = px.bar(
                    df_def,
                    x="valor",
                    y="defeito_tipo",
                    orientation="h",
                    title="<b>Perda Financeira por Tipologia de Defeito (R$)</b>",
                    color="valor",
                    color_continuous_scale="Reds",
                    labels={"valor": "Custo (R$)", "defeito_tipo": "Tipo de Defeito"}
                )
                fig_def.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_def, use_container_width=True)

        with g2:
            if "secao" in df_filtered.columns:
                df_sec = df_filtered.groupby("secao")["quantidade"].sum().reset_index()
                fig_sec = px.pie(
                    df_sec,
                    names="secao",
                    values="quantidade",
                    title="<b>Distribuição de Peças Refugadas por Seção</b>",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_sec.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_sec, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

# ---------------------------------------------------------
# TAB 2: REGISTRO DE DADOS
# ---------------------------------------------------------
with tab2:
    st.subheader("Cadastrar Ocorrência de Refugo")
    st.markdown("Preencha as informações abaixo para alimentar o sistema em tempo real.")

    with st.form("form_refugo", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            secao = st.text_input("Seção / Setor", placeholder="Ex: Usinagem")
            turno = st.selectbox("Turno", ["1º Turno", "2º Turno", "3º Turno", "Geral"])
            defeito_tipo = st.text_input("Tipo do Defeito", placeholder="Ex: Dimensional Fora")
        with c2:
            material = st.text_input("Código do Material", placeholder="Ex: MAT-10294")
            descricao_material = st.text_input("Descrição do Material", placeholder="Ex: Eixo Traseiro")
            nota = st.text_input("Número da Nota / Apontamento")
        with c3:
            quantidade = st.number_input("Quantidade Refugada", min_value=1, step=1)
            valor = st.number_input("Valor de Custo Total (R$)", min_value=0.0, format="%.2f")
            ct = st.text_input("Centro de Trabalho (CT)", placeholder="Ex: CT-04")

        observacao = st.text_area("Observações Técnicas", placeholder="Detalhes adicionais sobre a não-conformidade...")
        
        btn_salvar = st.form_submit_button("💾 Salvar Registro no Banco", use_container_width=True)

        if btn_salvar:
            if not secao or not defeito_tipo:
                st.error("Por favor, preencha os campos obrigatórios: Seção e Tipo de Defeito.")
            else:
                novo_registro = {
                    "secao": secao,
                    "turno": turno,
                    "defeito_tipo": defeito_tipo,
                    "material": material,
                    "descricao_material": descricao_material,
                    "nota": nota,
                    "quantidade": quantidade,
                    "valor": valor,
                    "ct": ct,
                    "observacao": observacao,
                    "data": datetime.date.today().strftime("%Y-%m-%d")
                }
                try:
                    supabase.table("refugos").insert(novo_registro).execute()
                    st.success("Registro adicionado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar registro: {e}")

# ---------------------------------------------------------
# TAB 3: BASE DE DADOS E TABELA INTERATIVA
# ---------------------------------------------------------
with tab3:
    st.subheader("Base Geral de Apontamentos")
    st.markdown("Consulte e acompanhe todas as entradas cadastradas.")
    if not df_filtered.empty:
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "quantidade": st.column_config.NumberColumn("Qtd (pcs)"),
                "data": st.column_config.DateColumn("Data")
            }
        )
    else:
        st.info("Sem dados disponíveis na base de dados.")
