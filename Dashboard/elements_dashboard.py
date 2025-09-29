import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_elements import elements, dashboard, mui, html

# Usaremos os mesmos dados do seu app principal para o exemplo
@st.cache_data
def carregar_dados_exemplo():
    # Simulando um dataframe parecido com o seu df_dia
    data = {
        'Espécie': ['Salminus brasiliensis', 'Prochilodus lineatus', 'Leporinus elongatus', 'Salminus brasiliensis', 'Oreochromis niloticus'],
        'N°_Individuos': [5, 12, 8, 2, 15],
        'Destino': ['Vivo', 'Vivo', 'Eutanasiado/Recolhido', 'Eutanasiado/Recolhido', 'Eutanasiado/Recolhido'],
        'Distribuição': ['Nativo', 'Nativo', 'Nativo', 'Nativo', 'Exótico']
    }
    return pd.DataFrame(data)

df_dia = carregar_dados_exemplo()

# Define o título da página
st.set_page_config(layout="wide")
st.title("Exemplo de Dashboard com Streamlit-Elements")

# ==========================================================
# AQUI COMEÇA A MÁGICA DO STREAMLIT-ELEMENTS
# ==========================================================

# 1. Criamos um "painel de controle" para todos os elementos
with elements("meu_dashboard_arrastavel"):

    # 2. Definimos o layout da grade. Cada item é um painel.
    # Você define a posição (x, y) e o tamanho (w, h) iniciais de cada painel.
    # A grade tem 12 colunas de largura.
    layout = [
        # Painel do KPI 1: Posição x=0, y=0, Largura=3, Altura=2
        dashboard.Item("kpi_total", 0, 0, 3, 2),
        # Painel do KPI 2: Posição x=3, y=0, Largura=3, Altura=2
        dashboard.Item("kpi_vivos", 3, 0, 3, 2),
        # Painel do Gráfico de Pizza: Posição x=0, y=2, Largura=6, Altura=4
        dashboard.Item("grafico_pizza", 0, 2, 6, 4),
        # Painel do Gráfico de Barras: Posição x=6, y=0, Largura=6, Altura=6
        dashboard.Item("grafico_barras", 6, 0, 6, 6),
    ]

    # 3. Criamos a grade do dashboard, passando o layout definido acima.
    # O `draggableHandle` permite especificar uma "alça" para arrastar, se quisermos.
    with dashboard.Grid(layout, draggableHandle=".draggable"):

        # 4. AGORA, PREENCHEMOS CADA PAINEL COM CONTEÚDO
        
        # --- Painel KPI 1 ---
        with mui.Card(key="kpi_total", sx={"display": "flex", "flexDirection": "column"}):
            # Adicionamos uma "alça" no topo para arrastar o painel
            mui.CardHeader(title="Total de Indivíduos", className="draggable")
            with mui.CardContent(sx={"flex": 1}):
                total_dia = int(df_dia['N°_Individuos'].sum())
                # Usamos o `html.h1` da biblioteca para formatar o número
                html.h1(f"{total_dia}", style={"textAlign": "center"})

        # --- Painel KPI 2 ---
        with mui.Card(key="kpi_vivos", sx={"display": "flex", "flexDirection": "column"}):
            mui.CardHeader(title="Indivíduos Vivos", className="draggable")
            with mui.CardContent(sx={"flex": 1}):
                vivos_dia = int(df_dia[df_dia['Destino'] == 'Vivo']['N°_Individuos'].sum())
                html.h1(f"{vivos_dia}", style={"textAlign": "center"})
        
        # --- Painel Gráfico de Pizza ---
        with mui.Card(key="grafico_pizza"):
            mui.CardHeader(title="Proporção por Destino", className="draggable")
            with mui.CardContent():
                df_destino_dia = df_dia.groupby('Destino')['N°_Individuos'].sum().reset_index()
                fig_pie_dia = px.pie(
                    df_destino_dia, values='N°_Individuos', names='Destino',
                    color_discrete_map={'Vivo': 'royalblue', 'Eutanasiado/Recolhido': 'darkred'}
                )
                st.plotly_chart(fig_pie_dia, use_container_width=True)

        # --- Painel Gráfico de Barras ---
        with mui.Card(key="grafico_barras"):
            mui.CardHeader(title="Contagem por Espécie", className="draggable")
            with mui.CardContent():
                fig_barras = px.bar(df_dia, x="N°_Individuos", y="Espécie", color="Destino", orientation='h')
                fig_barras.update_yaxes(tickfont=dict(style='italic'))
                st.plotly_chart(fig_barras, use_container_width=True)