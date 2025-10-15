import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime, date
import os
import base64
import locale
import gspread
from google.oauth2.service_account import Credentials
from github import Github

# --- Configuração de Idioma ---
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    pass

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# FUNÇÕES DE CONEXÃO E AUTENTICAÇÃO
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

@st.cache_resource(ttl=600)
def connect_to_google_sheets():
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"].to_dict()
    creds_dict["private_key"] = st.secrets["private_key_google"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

@st.cache_resource
def get_github_repo():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        return repo
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar com o GitHub: {e}")
        return None

def upload_to_github(repo, file_path, content, commit_message):
    try:
        repo.create_file(file_path, commit_message, content)
        st.sidebar.success(f"Arquivo '{os.path.basename(file_path)}' enviado!")
    except Exception as e:
        if e.status == 422:
            st.sidebar.warning(f"Arquivo '{os.path.basename(file_path)}' já existe. Não foi enviado novamente.")
        else:
            st.sidebar.error(f"Falha ao enviar '{os.path.basename(file_path)}': {e}")

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# CONFIGURAÇÃO GERAL E CARREGAMENTO DE DADOS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
st.set_page_config(page_title="Acompanhamento Ambiental - PCH Senhora do Porto", page_icon="y", layout="wide")

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

@st.cache_data(ttl=300)
def carregar_dados_completos():
    try:
        client = connect_to_google_sheets()
        spreadsheet = client.open("Dados_Resgate_PCH")

        sheet_ictio = spreadsheet.worksheet("dados_brutos")
        data = sheet_ictio.get_all_values()
        headers = data.pop(0) if data else []
        df_ictio = pd.DataFrame(data, columns=headers)
        df_ictio = df_ictio.loc[:, df_ictio.columns.notna() & (df_ictio.columns != '')]
        
        required_cols_ictio = ['Data', 'N°_Individuos', 'Biomassa_(g)', 'Destino', 'Resgate', 'Espécie', 'Distribuição', 'Latitude', 'Longitude', 'Ponto_Amostral']
        for col in required_cols_ictio:
            if col not in df_ictio.columns:
                df_ictio[col] = None
        
        df_ictio = df_ictio.astype(str).replace('', None).replace('nan', None).replace('<NA>', None)
        
        df_ictio['Data'] = pd.to_datetime(df_ictio['Data'], errors='coerce')
        df_ictio.dropna(subset=['Data'], inplace=True)
        cols_numericas_ictio = ['N°_Individuos', 'Biomassa_(g)']
        for col in cols_numericas_ictio:
            df_ictio[col] = pd.to_numeric(df_ictio[col], errors='coerce').fillna(0)
        
        df_ictio['Destino'] = df_ictio['Destino'].fillna('VAZIO').astype(str)
        condicoes_validas = ['Vivo', 'Eutanasiado/Recolhido']
        df_ictio = df_ictio[df_ictio['Destino'].isin(condicoes_validas)]
        for col in ['Resgate', 'Espécie', 'Distribuição']:
            df_ictio[col] = df_ictio[col].fillna('Não especificado').astype(str)

        sheet_abiotico = spreadsheet.worksheet("dados_abióticos")
        data_abio = sheet_abiotico.get_all_values()
        headers_abio = data_abio.pop(0) if data_abio else []
        df_abiotico = pd.DataFrame(data_abio, columns=headers_abio)
        df_abiotico = df_abiotico.loc[:, df_abiotico.columns.notna() & (df_abiotico.columns != '')]
        
        df_abiotico['Data'] = pd.to_datetime(df_abiotico['Data'], errors='coerce')
        df_abiotico.dropna(subset=['Data'], inplace=True)
        cols_numericas_abiotico = ['Oxigênio', 'Temperatura', 'pH', 'Nível']
        for col in cols_numericas_abiotico:
            df_abiotico[col] = pd.to_numeric(df_abiotico[col], errors='coerce').fillna(0)
        
        return df_ictio, df_abiotico
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha 'Dados_Resgate_PCH' não encontrada. Verifique o nome e as permissões de compartilhamento.")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def get_base64_from_github(_repo, file_path):
    try:
        content = _repo.get_contents(file_path)
        return base64.b64encode(content.decoded_content).decode()
    except Exception:
        return None

repo = get_github_repo()
logo_base64 = get_base64_from_github(repo, "assets/logo.png") if repo else None
df_ictio_master, df_abiotico_master = carregar_dados_completos()

if df_ictio_master.empty: 
    st.warning("Não foram encontrados dados de resgate válidos na planilha ou a planilha está vazia.")
    st.stop()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# BARRA LATERAL (SIDEBAR)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
if logo_base64:
    st.sidebar.image(f"data:image/png;base64,{logo_base64}")

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
if st.sidebar.button("♻️ Atualizar Dados da Planilha"): 
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📤 Enviar Fotos de Campo")
data_foto = st.sidebar.date_input("Selecione a data das fotos", value=date.today())
uploaded_files = st.sidebar.file_uploader("Escolha os arquivos de imagem", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

if st.sidebar.button("Enviar Fotos para o Repositório"):
    if uploaded_files:
        if repo:
            folder_path = f"fotos_atividades/{data_foto.strftime('%Y-%m-%d')}"
            commit_message = f"Upload de fotos via app para o dia {data_foto.strftime('%d/%m/%Y')}"
            
            with st.spinner("Enviando arquivos para o GitHub..."):
                for uploaded_file in uploaded_files:
                    file_content = uploaded_file.getvalue()
                    file_path_in_repo = f"{folder_path}/{uploaded_file.name}"
                    upload_to_github(repo, file_path_in_repo, file_content, commit_message)
            st.sidebar.info("Atualização concluída! As fotos podem levar alguns minutos para aparecer.")
    else:
        st.sidebar.warning("Por favor, selecione pelo menos um arquivo de foto.")

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
    # O restante do corpo do dashboard (KPIs, gráficos, mapa)
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
        st.subheader("Biomassa de NATIVOS Manejada ao Longo do Tempo")
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
            fig_temporal.add_vline(x=start_date, line_width=2, line_dash="dash", line_color="grey")
            fig_temporal.add_annotation(x=start_date, y=1, yref="paper", text="Dia Selecionado", showarrow=False, font=dict(color="grey"), bgcolor="rgba(255,255,255,0.5)", xshift=10, yshift=10)
            fig_temporal.update_xaxes(tickformat='%d %b %Y') 
        else:
            fig_temporal.update_xaxes(tickmode='linear', dtick='D1', tickformat='%d/%m')
        
        fig_temporal.update_layout(title_x=0.5, height=400, legend_title_text='Condição', yaxis_title="Biomassa (g)")
        st.plotly_chart(fig_temporal, use_container_width=True)

    with st.container(border=True):
        data_para_fotos = end_date if tipo_analise == "Período" else start_date
        st.subheader(f"Registros Fotográficos de {data_para_fotos.strftime('%d/%m/%Y')}")
        
        if repo:
            try:
                path_fotos = f"fotos_atividades/{data_para_fotos.strftime('%Y-%m-%d')}"
                contents = repo.get_contents(path_fotos)
                imagens = [file for file in contents if file.name.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                if not imagens:
                    st.info("Nenhum registro fotográfico encontrado para esta data no repositório.")
                else:
                    cols_fotos = st.columns(min(len(imagens), 4))
                    for i, img_content in enumerate(imagens):
                        with cols_fotos[i % 4]:
                            st.image(img_content.download_url, caption=img_content.name, use_container_width=True)
            except Exception:
                st.info("Nenhuma pasta de fotos encontrada para esta data no repositório.")
        else:
            st.warning("Não foi possível conectar ao GitHub para buscar as fotos.")

    with st.container(border=True):
        st.subheader("Mapa de Atividades de NATIVOS (Biomassa por Condição)")
        df_coords = df_ictio_periodo.copy()
        df_coords = df_coords[df_coords['Distribuição'] == 'Nativo']
        df_coords.rename(columns={'Destino': 'Condição'}, inplace=True)
        
        # --- CORREÇÃO DEFINITIVA DO MAPA: Função robusta para limpar coordenadas ---
        def clean_coord(coord_str):
            if not isinstance(coord_str, str):
                return None
            # Remove todos os pontos e depois substitui a última vírgula por um ponto decimal
            cleaned_str = coord_str.replace('.', '')
            if ',' in cleaned_str:
                parts = cleaned_str.rsplit(',', 1)
                cleaned_str = '.'.join(parts)
            return pd.to_numeric(cleaned_str, errors='coerce')

        df_coords['Latitude_num'] = df_coords['Latitude'].apply(clean_coord)
        df_coords['Longitude_num'] = df_coords['Longitude'].apply(clean_coord)
        
        df_mapa = df_coords.groupby(['Ponto_Amostral', 'Latitude_num', 'Longitude_num', 'Condição'])['Biomassa_(g)'].sum().reset_index()
        df_mapa.dropna(subset=['Latitude_num', 'Longitude_num'], inplace=True)
        
        if not df_mapa.empty:
            center_lat = df_mapa['Latitude_num'].mean()
            center_lon = df_mapa['Longitude_num'].mean()
            
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

