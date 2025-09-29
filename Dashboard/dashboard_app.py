import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import os
import base64
import locale

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# CONFIGURAÇÃO GERAL E CARREGAMENTO DE DADOS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
st.set_page_config(
    page_title="Acompanhamento Ambiental - PCH Senhora do Porto",
    page_icon="y",
    layout="wide"
)

# --- PALETA DE CORES E ESTILOS ---
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
        
        df_ictio['Destino'] = df_ictio['Destino'].fillna('VAZIO').astype(str)
        condicoes_validas = ['Vivo', 'Eutanasiado/Recolhido']
        df_ictio = df_ictio[df_ictio['Destino'].isin(condicoes_validas)]

        for col in ['Resgate', 'Espécie', 'Distribuição']:
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
if df_ictio_master.empty: 
    st.warning("Não foram encontrados dados de resgate válidos (com condição 'Vivo' ou 'Eutanasiado/Recolhido') na planilha.")
    st.stop()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# BARRA LATERAL (SIDEBAR)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
logo_path = BASE_DIR / "assets" / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path))

st.sidebar.header("Filtros do Relatório")
tipo_analise = st.sidebar.radio("Selecione o tipo de análise:", ("Dia Específico", "Período"))

if tipo_analise == "Dia Específico":
    data_selecionada = st.sidebar.date_input("Selecione a Data:", value=df_ictio_master['Data'].max().date(),
                                             min_value=df_ictio_master['Data'].min().date(), max_value=df_ictio_master['Data'].max().date())
    start_date = data_selecionada; end_date = data_selecionada
else:
    start_date_default = df_ictio_master['Data'].max().date() - pd.Timedelta(days=7)
    end_date_default = df_ictio_master['Data'].max().date()
    periodo_selecionado = st.sidebar.date_input("Selecione o Período:", value=(start_date_default, end_date_default),
                                                min_value=df_ictio_master['Data'].min().date(), max_value=df_ictio_master['Data'].max().date())
    if len(periodo_selecionado) == 2: start_date, end_date = periodo_selecionado
    else: start_date = end_date = periodo_selecionado[0]

fases_disponiveis = df_ictio_master['Resgate'].unique()
fase_selecionada = st.sidebar.multiselect("Selecione a(s) Fase(s) do Resgate:", options=fases_disponiveis, default=fases_disponiveis)
st.sidebar.markdown("---")
if st.sidebar.button("♻️ Atualizar Dados da Planilha"): st.cache_data.clear(); st.rerun()

# --- Filtragem de Dados ---
mask_ictio = (df_ictio_master['Data'].dt.date >= start_date) & (df_ictio_master['Data'].dt.date <= end_date) & (df_ictio_master['Resgate'].isin(fase_selecionada))
df_ictio_periodo = df_ictio_master[mask_ictio]
if not df_abiotico_master.empty:
    mask_abiotico = (df_abiotico_master['Data'].dt.date >= start_date) & (df_abiotico_master['Data'].dt.date <= end_date)
    df_abiotico_periodo = df_abiotico_master[mask_abiotico]
else:
    df_abiotico_periodo = pd.DataFrame()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# CORPO PRINCIPAL DO DASHBOARD
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
logo_base64 = get_image_as_base64(BASE_DIR / "assets" / "logo.png")
if logo_base64:
    st.markdown(f'<div class="header"><img src="data:image/png;base64,{logo_base64}" class="header-logo"><div class="header-title">Acompanhamento Ambiental - PCH Senhora do Porto</div></div>', unsafe_allow_html=True)

CHART_COLOR_PALETTE = {'Vivo': '#1E8449', 'Eutanasiado/Recolhido': '#C00000'}

if start_date == end_date:
    st.markdown(f"<div class='section-header'>Resultados do dia: {start_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='section-header'>Resultados do Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

if df_ictio_periodo.empty:
    st.warning("Nenhuma atividade de resgate registrada para este período com os filtros selecionados.")
else:
    total_biomassa_g = df_ictio_periodo['Biomassa_(g)'].sum()
    vivos_biomassa_g = df_ictio_periodo[df_ictio_periodo['Destino'] == 'Vivo']['Biomassa_(g)'].sum()
    
    df_nativos_periodo = df_ictio_periodo[df_ictio_periodo['Distribuição'] == 'Nativo']
    total_biomassa_nativos_g = df_nativos_periodo['Biomassa_(g)'].sum()
    vivos_biomassa_nativos_g = df_nativos_periodo[df_nativos_periodo['Destino'] == 'Vivo']['Biomassa_(g)'].sum()
    
    taxa_sobrevivencia_nativos = (vivos_biomassa_nativos_g / total_biomassa_nativos_g * 100) if total_biomassa_nativos_g > 0 else 0
    
    nivel_medio_periodo = None
    if not df_abiotico_periodo.empty: nivel_medio_periodo = df_abiotico_periodo['Nível'].mean()

    total_biomassa_kg = total_biomassa_g / 1000
    vivos_biomassa_kg = vivos_biomassa_g / 1000

    if start_date == end_date:
        diferenca_nivel = None
        data_anterior = start_date - pd.Timedelta(days=1)
        df_abiotico_anterior = df_abiotico_master[df_abiotico_master['Data'].dt.date == data_anterior]
        if not df_abiotico_anterior.empty and nivel_medio_periodo is not None:
            nivel_anterior = df_abiotico_anterior['Nível'].mean()
            diferenca_nivel = nivel_medio_periodo - nivel_anterior
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1, st.container(border=True): st.metric("Biomassa Total Manejada", f"{total_biomassa_kg:.2f} kg")
        with col2, st.container(border=True): st.metric("Biomassa Viva", f"{vivos_biomassa_kg:.2f} kg")
        with col3, st.container(border=True): st.metric("Taxa de Sobrev. (Nativos)", f"{taxa_sobrevivencia_nativos:.1f}%")
        with col4, st.container(border=True): st.metric("Nível Médio do Dia", f"{nivel_medio_periodo:.2f} m" if nivel_medio_periodo is not None else "N/A")
        with col5, st.container(border=True): st.metric("Rebaixamento (24h)", f"{diferenca_nivel:.2f} m" if diferenca_nivel is not None else "N/A", help="Diferença em relação ao dia anterior.")
    else:
        dias_com_atividade = df_ictio_periodo['Data'].dt.date.nunique()
        col1, col2, col3, col4 = st.columns(4)
        with col1, st.container(border=True): st.metric("Biomassa Total no Período", f"{total_biomassa_kg:.2f} kg")
        with col2, st.container(border=True): st.metric("Taxa de Sobrev. (Nativos)", f"{taxa_sobrevivencia_nativos:.1f}%")
        with col3, st.container(border=True): st.metric("Nível Médio no Período", f"{nivel_medio_periodo:.2f} m" if nivel_medio_periodo is not None else "N/A")
        with col4, st.container(border=True): st.metric("Dias com Atividade", f"{dias_com_atividade}")

    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1, st.container(border=True):
        st.subheader("Biomassa por Distribuição e Condição")
        df_dist = df_ictio_periodo.groupby(['Distribuição', 'Destino'])['Biomassa_(g)'].sum().reset_index()
        df_dist.rename(columns={'Destino': 'Condição'}, inplace=True)
        fig_dist = px.bar(df_dist, x='Distribuição', y='Biomassa_(g)', color='Condição', title="<b>Biomassa (g) por Distribuição e Condição</b>", color_discrete_map=CHART_COLOR_PALETTE)
        fig_dist.update_layout(title_x=0.5, height=400, yaxis_title="Biomassa (g)")
        st.plotly_chart(fig_dist, use_container_width=True)
    with col_graf2, st.container(border=True):
        st.subheader("Top 10 Espécies por Biomassa")
        top_10_list = df_ictio_periodo.groupby('Espécie')['Biomassa_(g)'].sum().nlargest(10).index
        df_top10_raw = df_ictio_periodo[df_ictio_periodo['Espécie'].isin(top_10_list)]
        if not df_top10_raw.empty:
            df_top10 = df_top10_raw.copy()
            df_top10.rename(columns={'Destino': 'Condição'}, inplace=True)
            fig_top10 = px.bar(df_top10, y='Espécie', x='Biomassa_(g)', color='Condição', orientation='h', title="<b>Composição por Biomassa (g)</b>", color_discrete_map=CHART_COLOR_PALETTE)
            fig_top10.update_yaxes(categoryorder='total ascending', tickfont=dict(style='italic'))
            fig_top10.update_layout(title_x=0.5, height=400, xaxis_title="Biomassa (g)")
            st.plotly_chart(fig_top10, use_container_width=True)
    
    with st.container(border=True):
        st.subheader("Biomassa de Nativos ao Longo do Tempo")
        df_temporal_raw = df_ictio_periodo.copy()
        if tipo_analise == "Dia Específico":
            df_temporal_raw = df_ictio_master[df_ictio_master['Resgate'].isin(fase_selecionada)].copy()
        
        df_temporal_raw = df_temporal_raw[df_temporal_raw['Distribuição'] == 'Nativo']
        
        df_temporal_raw.rename(columns={'Destino': 'Condição'}, inplace=True)
        df_temporal = df_temporal_raw.groupby([df_temporal_raw['Data'].dt.date, 'Condição'])['Biomassa_(g)'].sum().reset_index()

        fig_temporal = px.bar(df_temporal, x='Data', y='Biomassa_(g)', color='Condição',
                              title="<b>Biomassa de Nativos (g) por Dia e Condição</b>",
                              color_discrete_map=CHART_COLOR_PALETTE)
        
        if tipo_analise == "Dia Específico":
            # --- CORREÇÃO DEFINITIVA: Destaque com linha vertical + texto separado ---
            fig_temporal.add_vline(x=start_date, line_width=2, line_dash="dash", line_color="grey")
            fig_temporal.add_annotation(
                x=start_date, y=1, yref="paper", 
                text="Dia Selecionado", showarrow=False,
                font=dict(color="grey"), bgcolor="rgba(255,255,255,0.5)",
                xshift=10, yshift=10
            )
            fig_temporal.update_xaxes(tickformat='%d %b %Y') 
        else:
            fig_temporal.update_xaxes(tickmode='linear', dtick='D1', tickformat='%d/%m')
        
        fig_temporal.update_layout(title_x=0.5, height=400, legend_title_text='Condição', yaxis_title="Biomassa (g)")
        st.plotly_chart(fig_temporal, use_container_width=True)

    if tipo_analise == "Período":
         with st.container(border=True):
            st.subheader(f"Registros Fotográficos de {end_date.strftime('%d/%m/%Y')}")
            data_str_pasta = end_date.strftime('%Y-%m-%d')
            pasta_fotos_dia = FOTOS_DIR / data_str_pasta
            imagens_encontradas = list(pasta_fotos_dia.glob("*.jpg")) + list(pasta_fotos_dia.glob("*.png")) + list(pasta_fotos_dia.glob("*.jpeg"))
            if not imagens_encontradas:
                st.info("Nenhum registro fotográfico para o último dia do período.")
            else:
                cols_fotos = st.columns(2)
                if len(imagens_encontradas) > 0:
                    with cols_fotos[0]: st.image(str(imagens_encontradas[0]), use_container_width=True)
                if len(imagens_encontradas) > 1:
                    with cols_fotos[1]: st.image(str(imagens_encontradas[1]), use_container_width=True)
    elif start_date == end_date:
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
        st.subheader("Mapa de Atividades de Nativos (Biomassa por Condição)")
        df_coords = df_ictio_periodo.copy()
        
        df_coords = df_coords[df_coords['Distribuição'] == 'Nativo']
        
        df_coords.rename(columns={'Destino': 'Condição'}, inplace=True)
        df_coords['Latitude_num'] = pd.to_numeric(df_coords['Latitude'].astype(str).str.replace('°', ''), errors='coerce')
        df_coords['Longitude_num'] = pd.to_numeric(df_coords['Longitude'].astype(str).str.replace('°', ''), errors='coerce')
        
        df_mapa = df_coords.groupby(['Ponto_Amostral', 'Latitude_num', 'Longitude_num', 'Condição'])['Biomassa_(g)'].sum().reset_index()
        df_mapa.dropna(subset=['Latitude_num', 'Longitude_num'], inplace=True)
        
        if not df_mapa.empty:
            center_lat = df_mapa['Latitude_num'].mean()
            center_lon = df_mapa['Longitude_num'].mean()
            px.set_mapbox_access_token(MAPBOX_TOKEN)
            
            fig_mapa = px.scatter_mapbox(df_mapa, lat="Latitude_num", lon="Longitude_num", 
                                         size="Biomassa_(g)", 
                                         color="Condição", 
                                         hover_name="Ponto_Amostral",
                                         color_discrete_map=CHART_COLOR_PALETTE,
                                         hover_data={"Biomassa_(g)": ':.2f', "Latitude_num": False, "Longitude_num": False},
                                         mapbox_style="satellite-streets", 
                                         center=dict(lat=center_lat, lon=center_lon), 
                                         zoom=15,
                                         size_max=20)
                                         
            fig_mapa.update_layout(height=500, margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text='Condição')
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:

            st.warning("Nenhum dado de coordenada de NATIVOS encontrado com os filtros selecionados.")
