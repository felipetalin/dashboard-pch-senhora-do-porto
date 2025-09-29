import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import os

# --- 1. DADOS E GRÁFICO DE EXEMPLO ---

# Criamos um dataframe simples para simular seus dados
df_exemplo = pd.DataFrame({
    'Espécie': ['Salminus brasiliensis', 'Prochilodus lineatus', 'Leporinus elongatus', 'Hoplias malabaricus'],
    'N°_Individuos': [15, 28, 12, 22],
    'Destino': ['Vivo', 'Vivo', 'Eutanasiado/Recolhido', 'Vivo']
})

# Criamos um gráfico de exemplo com o Plotly
fig = px.bar(
    df_exemplo, 
    y='Espécie', 
    x='N°_Individuos', 
    color='Destino', 
    orientation='h',
    title="<b>Composição de Espécies da Amostragem</b>",
    color_discrete_map={'Vivo': '#1E8449', 'Eutanasiado/Recolhido': '#D32F2F'}
)
fig.update_yaxes(categoryorder='total ascending', tickfont=dict(style='italic'), title=None)
fig.update_layout(title_x=0.5, height=350, margin=dict(l=10, r=10, t=40, b=10))

# --- 2. FUNÇÃO PRINCIPAL PARA CRIAR O PDF ---

def criar_relatorio_pdf(df, fig):
    """
    Constrói um relatório PDF A4 com KPIs e um gráfico salvo como imagem.
    """
    
    # Define o caminho do arquivo de imagem temporário
    grafico_path = "grafico_temp.png"
    
    # Bloco try...finally para garantir que a imagem temporária seja sempre deletada
    try:
        # --- ETAPA A: Salvar o gráfico como uma imagem ---
        # scale=2 aumenta a resolução para uma melhor qualidade no PDF
        fig.write_image(grafico_path, width=800, height=350, scale=2)
        
        # --- ETAPA B: Construir o PDF ---
        pdf = FPDF(orientation='P', unit='mm', format='A4') # P = Retrato
        pdf.add_page()
        
        # Cabeçalho
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Relatório de Teste de Ictiofauna', 0, 1, 'C')
        pdf.ln(10) # Pula uma linha
        
        # KPIs
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Indicadores Resumidos', 0, 1, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f"- Total de Indivíduos Manejados: {df['N°_Individuos'].sum()}", 0, 1, 'L')
        pdf.cell(0, 8, f"- Total de Espécies Registradas: {df['Espécie'].nunique()}", 0, 1, 'L')
        pdf.ln(10)

        # Inserir a imagem do gráfico
        # A largura de uma página A4 é 210mm. Usamos 190mm para deixar margens.
        pdf.image(grafico_path, x=10, w=190)
        
        # Converte o PDF para bytes para o Streamlit poder fazer o download
        return bytes(pdf.output(dest='S'))
        
    finally:
        # --- ETAPA C: Limpeza ---
        # Garante que o arquivo de imagem temporário seja deletado, mesmo se ocorrer um erro
        if os.path.exists(grafico_path):
            os.remove(grafico_path)

# --- 3. INTERFACE DO STREAMLIT ---

st.title("Teste Final de Geração de PDF")

st.info("Este é um teste para validar a criação de um PDF A4 com gráficos a partir do Streamlit, usando as bibliotecas FPDF2 e Kaleido.")

st.subheader("Gráfico de Exemplo (Como aparece no Dashboard)")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

if st.button("📄 Gerar Relatório PDF Final"):
    with st.spinner("Gerando PDF..."):
        pdf_data = criar_relatorio_pdf(df_exemplo, fig)
        
        if pdf_data:
            st.download_button(
                label="✅ Download do PDF Pronto",
                data=pdf_data,
                file_name="relatorio_final.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Falha ao gerar o PDF.")