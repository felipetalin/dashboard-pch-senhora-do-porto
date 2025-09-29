import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import os
import base64

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# CONFIGURAÇÃO GERAL E CARREGAMENTO DE DADOS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
st.set_page_config(
    page_title="Acompanhamento Ambiental - PCH Senhora do Porto",
    page_icon="y",
    layout="wide"
)

# --- PALETA DE CORES VERDE ---
st.markdown("""
<style>
    .main { background-color: #F0FFF0; }
    [data-testid="stSidebar"] { background-color: #E6F3E6; }
    h1, h2, h3 { color: #006400; }
    .header { display: flex; justify-content: space-between; align-items: center; padding: 10px 25px; background-color: #E6F3E6; border-radius: 10px; margin-bottom: 20px; border: 1px solid #A9D9A9; }
    .header-logo { height: 50px; }
    .header-title { font-size: 24px; font-weight: bold; color: #006400; }
    .section-header { background-color: #A9D9A9; color: #006400; padding: 10px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
        border-radius: 10px; border: 1px solid #A9D9A9;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1); background-color: #F5FFFA;
        padding: 20px; margin-bottom: 20px;
    }
    div[data-testid="stMetric"] {
        background-color: #F5FFFA; border: 1px solid #F5FFFA;
        padding: 5px; border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

MAPBOX_TOKEN = "pk.eyJ1IjoiZmVsaXBldGFsaW4iLCJhIjoiY21mZm9pbG42MDhxczJqcHQ2azZhcTNtdCJ9.Ej4EtF8HH10mZraWnBC_mg"
BASE_DIR = Path(__file__).resolve().parent
PLANILHA_PATH = BASE_DIR.parent / "Dados-brutos-Resgate-Guanhães_2025.xlsx"
FOTOS_DIR = BASE_DIR.parent / "fotos_atividades"

@st.cache_data
def carregar_dados_completos():
    try:
        df_ictio = pd.read_excel(PLANILHA_PATH, sheet_name='dados_brutos')
        df_ictio['Data'] = pd.to_datetime(df_ictio['Data'], dayfirst=True, errors='coerce')
        df_ictio.dropna(subset=['Data'], inplace=True)
        cols_numericas_ictio = ['N°_Individuos', 'Biomassa_(g)']
        for col in cols_numericas_ictio:
            df_ictio[col] = pd.to_numeric(df_ictio[col], errors='coerce').fillna(0)
        for col in ['Resgate', 'Espécie', 'Destino', 'Distribuição']:
            df_ictio[col] = df_ictio[col].fillna('Não especificado').astype(str)

        df_abiotico = pd.read_excel(PLANILHA_PATH, sheet_name='dados_abióticos')
        df_abiotico['Data'] = pd.to_datetime(df_abiotico['Data'], dayfirst=True, errors='coerce')
        df_abiotico.dropna(subset=['Data'], inplace=True)
        cols_numericas_abiotico = ['Oxigênio', 'Temperatura', 'pH', 'Nível']
        for col in cols_numericas_abiotico:
            df_abiotico[col] = pd.to_numeric(df_abiotico[col], errors='coerce').fillna(0)
        return df_ictio, df_abiotico
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def get_image_as_base64(path):
    if path.exists():
        with open(path, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    return None

df_ictio_master, df_abiotico_master = carregar_dados_completos()
if df_ictio_master.empty: st.stop()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# BARRA LATERAL (SIDEBAR)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
logo_path = BASE_DIR / "assets" / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path))

st.sidebar.header("Filtros do Relatório")
tipo_analise = st.sidebar.radio("Selecione o tipo de análise:", ("Dia Específico", "Período"))

if tipo_analise == "Dia Específico":
    data_selecionada = st.sidebar.date_input("Selecione a Data:", value=df_ictio_master['Data'].max().date(), min_value=df_ictio_master['Data'].min().date(), max_value=df_ictio_master['Data'].max().date())
    start_date = data_selecionada; end_date = data_selecionada
else:
    start_date_default = df_ictio_master['Data'].max().date() - pd.Timedelta(days=7)
    end_date_default = df_ictio_master['Data'].max().date()
    periodo_selecionado = st.sidebar.date_input("Selecione o Período:", value=(start_date_default, end_date_default), min_value=df_ictio_master['Data'].min().date(), max_value=df_ictio_master['Data'].max().date())
    if len(periodo_selecionado) == 2: start_date, end_date = periodo_selecionado
    else: start_date = end_date = periodo_selecionado[0]

fases_disponiveis = df_ictio_master['Resgate'].unique()
fase_selecionada = st.sidebar.multiselect("Selecione a(s) Fase(s) do Resgate:", options=fases_disponiveis, default=fases_disponiveis)
st.sidebar.markdown("---")
if st.sidebar.button("♻️ Atualizar Dados da Planilha"): st.cache_data.clear(); st.rerun()

# --- NOVO: CONTROLE DO MODO RELATÓRIO ---
st.sidebar.markdown("---")
report_mode = st.sidebar.checkbox("📄 Ativar Modo Relatório (para impressão)")

# --- Filtragem de Dados ---
mask_ictio = (df_ictio_master['Data'].dt.date >= start_date) & (df_ictio_master['Data'].dt.date <= end_date) & (df_ictio_master['Resgate'].isin(fase_selecionada))
df_ictio_periodo = df_ictio_master[mask_ictio]
if not df_abiotico_master.empty:
    mask_abiotico = (df_ictio_master['Data'].dt.date >= start_date) & (df_ictio_master['Data'].dt.date <= end_date)
    df_abiotico_periodo = df_abiotico_master[mask_abiotico]
else:
    df_abiotico_periodo = pd.DataFrame()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# CORPO PRINCIPAL DO DASHBOARD
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
logo_base64 = get_image_as_base64(BASE_DIR / "assets" / "logo.png")
if logo_base64 and not report_mode: # Esconde o cabeçalho no modo relatório
    st.markdown(f'<div class="header"><img src="data:image/png;base64,{logo_base64}" class="header-logo"><div class="header-title">Acompanhamento Ambiental - PCH Senhora do Porto</div></div>', unsafe_allow_html=True)

CHART_COLOR_PALETTE = {'Vivo': '#1E8449', 'Eutanasiado/Recolhido': '#D32F2F', 'Não especificado': '#808080'}

# --- LAYOUT CONDICIONAL ---
if report_mode:
    # =========================================================
    # LAYOUT VERTICAL OTIMIZADO PARA IMPRESSÃO (MODO RELATÓRIO)
    # =========================================================
    st.markdown(f"<div class='section-header'>Relatório do Dia: {start_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
    
    if df_ictio_periodo.empty or start_date != end_date:
        st.warning("O Modo Relatório só está disponível para a análise de 'Dia Específico' e com dados no dia selecionado.")
    else:
        with st.container(border=True):
            st.subheader("Resumo do Dia")
            total_periodo = int(df_ictio_periodo['N°_Individuos'].sum())
            vivos_periodo = int(df_ictio_periodo[df_ictio_periodo['Destino'] == 'Vivo']['N°_Individuos'].sum())
            df_nativos_periodo = df_ictio_periodo[df_ictio_periodo['Distribuição'] == 'Nativo']
            total_nativos_periodo = df_nativos_periodo['N°_Individuos'].sum()
            vivos_nativos_periodo = df_nativos_periodo[df_nativos_periodo['Destino'] == 'Vivo']['N°_Individuos'].sum()
            taxa_sobrevivencia_nativos = (vivos_nativos_periodo / total_nativos_periodo * 100) if total_nativos_periodo > 0 else 0
            nivel_medio_periodo = None
            diferenca_nivel = None
            if not df_abiotico_periodo.empty:
                nivel_medio_periodo = df_abiotico_periodo['Nível'].mean()
                data_anterior = start_date - pd.Timedelta(days=1)
                df_abiotico_anterior = df_abiotico_master[df_abiotico_master['Data'].dt.date == data_anterior]
                if not df_abiotico_anterior.empty:
                    nivel_anterior = df_abiotico_anterior['Nível'].mean()
                    diferenca_nivel = nivel_medio_periodo - nivel_anterior
            
            # KPIs organizados para A4
            kpi_col1, kpi_col2 = st.columns(2)
            kpi_col3, kpi_col4, kpi_col5 = st.columns(3)
            with kpi_col1: st.metric("Total Indivíduos Manejados", f"{total_periodo}")
            with kpi_col2: st.metric("Total Indivíduos Vivos", f"{vivos_periodo}")
            with kpi_col3: st.metric("Taxa de Sobrev. (Nativos)", f"{taxa_sobrevivencia_nativos:.1f}%")
            with kpi_col4: st.metric("Nível Médio do Dia", f"{nivel_medio_periodo:.2f} m" if nivel_medio_periodo is not None else "N/A")
            with kpi_col5: st.metric("Rebaixamento (24h)", f"{diferenca_nivel:.2f} m" if diferenca_nivel is not None else "N/A")

        with st.container(border=True):
            st.subheader("Registros Fotográficos do Dia")
            data_str_pasta = start_date.strftime('%Y-%m-%d')
            pasta_fotos_dia = FOTOS_DIR / data_str_pasta
            imagens_encontradas = list(pasta_fotos_dia.glob("*.jpg")) + list(pasta_fotos_dia.glob("*.png")) + list(pasta_fotos_dia.glob("*.jpeg"))
            if not imagens_encontradas:
                st.info("Nenhum registro fotográfico encontrado para esta data.")
            else:
                cols_fotos = st.columns(2) # Força a exibição de até 2 fotos
                if len(imagens_encontradas) > 0:
                    with cols_fotos[0]: st.image(str(imagens_encontradas[0]), caption=os.path.basename(imagens_encontradas[0]), use_container_width=True)
                if len(imagens_encontradas) > 1:
                    with cols_fotos[1]: st.image(str(imagens_encontradas[1]), caption=os.path.basename(imagens_encontradas[1]), use_container_width=True)
            
        with st.container(border=True):
            st.subheader("Top 5 Espécies do Dia")
            top_5_list = df_ictio_periodo.groupby('Espécie')['N°_Individuos'].sum().nlargest(5).index
            df_top5 = df_ictio_periodo[df_ictio_periodo['Espécie'].isin(top_5_list)]
            fig_top5 = px.bar(df_top5, y='Espécie', x='N°_Individuos', color='Destino', orientation='h', title="<b>Composição por Destino</b>", color_discrete_map=CHART_COLOR_PALETTE)
            fig_top5.update_yaxes(categoryorder='total ascending', tickfont=dict(style='italic'))
            fig_top5.update_layout(title_x=0.5, height=350, yaxis_title=None)
            st.plotly_chart(fig_top5, use_container_width=True)
            
        with st.container(border=True):
            st.subheader("Histórico de Resgates")
            df_ictio_acumulado = df_ictio_master[df_ictio_master['Data'].dt.date <= end_date] # Recalcula acumulado para o gráfico
            df_temporal_hist = df_ictio_acumulado.groupby(df_ictio_acumulado['Data'].dt.date)['N°_Individuos'].sum().reset_index()
            fig_temporal_hist = px.bar(df_temporal_hist, x='Data', y='N°_Individuos', title="<b>Total de Indivíduos Resgatados por Dia</b>", color_discrete_sequence=['#006400'])
            fig_temporal_hist.update_layout(title_x=0.5, height=350)
            st.plotly_chart(fig_temporal_hist, use_container_width=True)
else:
    # =========================================================
    # LAYOUT INTERATIVO NORMAL (O SEU CÓDIGO ATUAL)
    # =========================================================
    if start_date == end_date:
        st.markdown(f"<div class='section-header'>Resultados do dia: {start_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='section-header'>Resultados do Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

    if df_ictio_periodo.empty:
        st.warning("Nenhuma atividade de resgate registrada para este período com os filtros selecionados.")
    else:
        total_periodo = int(df_ictio_periodo['N°_Individuos'].sum())
        vivos_periodo = int(df_ictio_periodo[df_ictio_periodo['Destino'] == 'Vivo']['N°_Individuos'].sum())
        df_nativos_periodo = df_ictio_periodo[df_ictio_periodo['Distribuição'] == 'Nativo']
        total_nativos_periodo = df_nativos_periodo['N°_Individuos'].sum()
        vivos_nativos_periodo = df_nativos_periodo[df_nativos_periodo['Destino'] == 'Vivo']['N°_Individuos'].sum()
        taxa_sobrevivencia_nativos = (vivos_nativos_periodo / total_nativos_periodo * 100) if total_nativos_periodo > 0 else 0
        nivel_medio_periodo = None
        if not df_abiotico_periodo.empty: nivel_medio_periodo = df_abiotico_periodo['Nível'].mean()

        if start_date == end_date:
            diferenca_nivel = None
            data_anterior = start_date - pd.Timedelta(days=1)
            df_abiotico_anterior = df_abiotico_master[df_abiotico_master['Data'].dt.date == data_anterior]
            if not df_abiotico_anterior.empty and nivel_medio_periodo is not None:
                nivel_anterior = df_abiotico_anterior['Nível'].mean()
                diferenca_nivel = nivel_medio_periodo - nivel_anterior
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1, st.container(border=True): st.metric("Total Indivíduos Manejados", f"{total_periodo}")
            with col2, st.container(border=True): st.metric("Total Indivíduos Vivos", f"{vivos_periodo}")
            with col3, st.container(border=True): st.metric("Taxa de Sobrev. (Nativos)", f"{taxa_sobrevivencia_nativos:.1f}%")
            with col4, st.container(border=True): st.metric("Nível Médio do Dia", f"{nivel_medio_periodo:.2f} m" if nivel_medio_periodo is not None else "N/A")
            with col5, st.container(border=True): st.metric("Rebaixamento (24h)", f"{diferenca_nivel:.2f} m" if diferenca_nivel is not None else "N/A", help="Diferença em relação ao dia anterior.")
        else:
            dias_com_atividade = df_ictio_periodo['Data'].dt.date.nunique()
            col1, col2, col3, col4 = st.columns(4)
            with col1, st.container(border=True): st.metric("Total Indivíduos no Período", f"{total_periodo}")
            with col2, st.container(border=True): st.metric("Taxa de Sobrev. (Nativos)", f"{taxa_sobrevivencia_nativos:.1f}%")
            with col3, st.container(border=True): st.metric("Nível Médio no Período", f"{nivel_medio_periodo:.2f} m" if nivel_medio_periodo is not None else "N/A")
            with col4, st.container(border=True): st.metric("Dias com Atividade", f"{dias_com_atividade}")

        st.markdown("---")
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1, st.container(border=True):
            st.subheader("Distribuição e Destino")
            df_dist = df_ictio_periodo.groupby(['Distribuição', 'Destino'])['N°_Individuos'].sum().reset_index()
            fig_dist = px.bar(df_dist, x='Distribuição', y='N°_Individuos', color='Destino', text_auto=True, title="<b>Contagem por Distribuição e Destino</b>", color_discrete_map=CHART_COLOR_PALETTE)
            fig_dist.update_layout(title_x=0.5, height=400)
            st.plotly_chart(fig_dist, use_container_width=True)
        with col_graf2, st.container(border=True):
            st.subheader("Top 10 Espécies no Período")
            top_10_list = df_ictio_periodo.groupby('Espécie')['N°_Individuos'].sum().nlargest(10).index
            df_top10 = df_ictio_periodo[df_ictio_periodo['Espécie'].isin(top_10_list)]
            if not df_top10.empty:
                fig_top10 = px.bar(df_top10, y='Espécie', x='N°_Individuos', color='Destino', orientation='h', title="<b>Composição por Destino</b>", color_discrete_map=CHART_COLOR_PALETTE)
                fig_top10.update_yaxes(categoryorder='total ascending', tickfont=dict(style='italic'))
                fig_top10.update_layout(title_x=0.5, height=400)
                st.plotly_chart(fig_top10, use_container_width=True)
        
        with st.container(border=True):
            st.subheader("Resgates ao Longo do Tempo")
            df_temporal = df_ictio_periodo.groupby(df_ictio_periodo['Data'].dt.date)['N°_Individuos'].sum().reset_index()
            fig_temporal = px.line(df_temporal, x='Data', y='N°_Individuos', markers=True, title="<b>Total de Indivíduos por Dia</b>", color_discrete_sequence=['#006400'])
            fig_temporal.update_layout(title_x=0.5, height=400)
            st.plotly_chart(fig_temporal, use_container_width=True)

        if start_date == end_date:
            with st.container(border=True):
                st.subheader("Registros Fotográficos do Dia")
                data_str_pasta = start_date.strftime('%Y-%m-%d')
                pasta_fotos_dia = FOTOS_DIR / data_str_pasta
                imagens_encontradas = list(pasta_fotos_dia.glob("*.jpg")) + list(pasta_fotos_dia.glob("*.png")) + list(pasta_fotos_dia.glob("*.jpeg"))
                if not imagens_encontradas:
                    st.info("Nenhum registro fotográfico encontrado para esta data.")
                else:
                    cols_fotos = st.columns(len(imagens_encontradas))
                    for i, img_path in enumerate(imagens_encontradas):
                        if i < len(cols_fotos):
                            with cols_fotos[i]:
                                st.image(str(img_path), caption=os.path.basename(img_path), use_container_width=True)
        
        with st.container(border=True):
            st.subheader("Mapa de Atividades no Período")
            df_coords = df_ictio_periodo.copy()
            df_coords['Latitude_num'] = pd.to_numeric(df_coords['Latitude'].astype(str).str.replace('°', ''), errors='coerce')
            df_coords['Longitude_num'] = pd.to_numeric(df_coords['Longitude'].astype(str).str.replace('°', ''), errors='coerce')
            df_mapa = df_coords.groupby(['Ponto_Amostral', 'Latitude_num', 'Longitude_num'])['N°_Individuos'].sum().reset_index()
            df_mapa.dropna(subset=['Latitude_num', 'Longitude_num'], inplace=True)
            if not df_mapa.empty:
                center_lat = df_mapa['Latitude_num'].mean()
                center_lon = df_mapa['Longitude_num'].mean()
                px.set_mapbox_access_token(MAPBOX_TOKEN)
                fig_mapa = px.scatter_map(df_mapa, lat="Latitude_num", lon="Longitude_num", size="N°_Individuos", color="Ponto_Amostral", hover_name="Ponto_Amostral",
                    hover_data={"N°_Individuos": True, "Latitude_num": False, "Longitude_num": False},
                    map_style="satellite-streets", center=dict(lat=center_lat, lon=center_lon), zoom=15)
                fig_mapa.update_layout(height=500, margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_mapa, use_container_width=True)
            else:
                st.warning("Nenhum dado de coordenada encontrado com os filtros selecionados.")