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
    pass # Ignora o erro silenciosamente se a localidade não for encontrada

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# FUNÇÕES DE CONEXÃO E AUTENTICAÇÃO
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# Conexão com Google Sheets
@st.cache_resource(ttl=600) # Cache de 10 minutos
def connect_to_google_sheets():
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    return client

# Conexão com GitHub
def get_github_repo():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"]) # Ex: "seu-usuario/seu-repositorio"
        return repo
    except Exception as e:
        st.error(f"Erro ao conectar com o GitHub: {e}")
        return None

# Função para fazer upload de arquivos para o GitHub
def upload_to_github(repo, file_path, content, commit_message):
    try:
        # Tenta pegar o arquivo para ver se ele já existe e precisa ser atualizado
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_message, content, contents.sha)
        st.success(f"Arquivo '{os.path.basename(file_path)}' atualizado com sucesso!")
    except Exception:
        # Se não existe, cria um novo
        repo.create_file(file_path, commit_message, content)
        st.success(f"Arquivo '{os.path.basename(file_path)}' enviado com sucesso!")

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# CONFIGURAÇÃO GERAL E CARREGAMENTO DE DADOS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
st.set_page_config(page_title="Acompanhamento Ambiental - PCH Senhora do Porto", page_icon="y", layout="wide")

st.markdown("""
<style>
    /* ... (seu CSS continua o mesmo) ... */
</style>
""", unsafe_allow_html=True)

# --- Carregando dados do Google Sheets ---
@st.cache_data(ttl=600) # Cache de 10 minutos
def carregar_dados_completos():
    try:
        client = connect_to_google_sheets()
        spreadsheet = client.open("Dados_Resgate_PCH") # Nome da sua Planilha Google

        # Carrega dados brutos
        sheet_ictio = spreadsheet.worksheet("dados_brutos")
        df_ictio = pd.DataFrame(sheet_ictio.get_all_records())
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

        # Carrega dados abióticos
        sheet_abiotico = spreadsheet.worksheet("dados_abióticos")
        df_abiotico = pd.DataFrame(sheet_abiotico.get_all_records())
        df_abiotico['Data'] = pd.to_datetime(df_abiotico['Data'], errors='coerce')
        df_abiotico.dropna(subset=['Data'], inplace=True)
        cols_numericas_abiotico = ['Oxigênio', 'Temperatura', 'pH', 'Nível']
        for col in cols_numericas_abiotico:
            df_abiotico[col] = pd.to_numeric(df_abiotico[col], errors='coerce').fillna(0)
        
        return df_ictio, df_abiotico
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_ictio_master, df_abiotico_master = carregar_dados_completos()
if df_ictio_master.empty: 
    st.warning("Não foram encontrados dados de resgate válidos na planilha.")
    st.stop()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# BARRA LATERAL (SIDEBAR)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
logo_path = "assets/logo.png" # Caminho relativo no repositório
st.sidebar.image(logo_path)

st.sidebar.header("Filtros do Relatório")
# ... (o resto da sua sidebar de filtros continua o mesmo) ...

# --- NOVA SEÇÃO: UPLOAD DE FOTOS ---
st.sidebar.markdown("---")
st.sidebar.subheader("📤 Enviar Fotos de Campo")

data_foto = st.sidebar.date_input("Selecione a data das fotos", value=date.today())
uploaded_files = st.sidebar.file_uploader("Escolha os arquivos de imagem", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

if st.sidebar.button("Enviar Fotos para o Repositório"):
    if uploaded_files:
        repo = get_github_repo()
        if repo:
            folder_path = f"fotos_atividades/{data_foto.strftime('%Y-%m-%d')}"
            commit_message = f"Upload de fotos para o dia {data_foto.strftime('%d/%m/%Y')}"
            
            with st.spinner("Enviando arquivos..."):
                for uploaded_file in uploaded_files:
                    file_content = uploaded_file.getvalue()
                    file_path_in_repo = f"{folder_path}/{uploaded_file.name}"
                    upload_to_github(repo, file_path_in_repo, file_content, commit_message)
            st.sidebar.success("Todos os arquivos foram enviados!")
            st.sidebar.info("Os novos dados podem levar alguns minutos para aparecer no dashboard.")
    else:
        st.sidebar.warning("Por favor, selecione pelo menos um arquivo de foto.")

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# CORPO PRINCIPAL DO DASHBOARD
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# O corpo principal do seu dashboard (KPIs, gráficos, mapa) permanece EXATAMENTE O MESMO
# Vou colar ele aqui para garantir que o arquivo esteja completo.
# ... (Cole aqui o corpo principal do seu último código perfeito) ...

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

