import requests
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np
import os

# --- ETAPA 1: DEFINIR A ÁREA DE INTERESSE (AOI) ---

# Suas coordenadas como ponto central
ponto_central_lat = -19.035842
ponto_central_lon = -42.922628

# Definir o tamanho da "janela" ao redor do ponto central (0.05 graus ~= 5.5 km)
buffer_graus = 0.05 

# Calcular os limites da caixa (bounding box)
bounds = (
    ponto_central_lat - buffer_graus,  # Sul (South)
    ponto_central_lon - buffer_graus,  # Oeste (West)
    ponto_central_lat + buffer_graus,  # Norte (North)
    ponto_central_lon + buffer_graus   # Leste (East)
)

print(f"Analisando a área ao redor de Lat: {ponto_central_lat}, Lon: {ponto_central_lon}")

# --- ETAPA 2: OBTER OS DADOS DE ELEVAÇÃO ---

# O nome do arquivo de saída. Ele será salvo na mesma pasta que este script.
output_file = "minha_area_dem.tif"

# Checa se o arquivo já existe para não baixar novamente sem necessidade
if not os.path.exists(output_file):
    print(f"\nBaixando o Modelo Digital de Elevação para '{output_file}'...")
    api_url = f"https://portal.opentopography.org/API/globaldem?demtype=COP30&south={bounds[0]}&north={bounds[2]}&west={bounds[1]}&east={bounds[3]}&outputFormat=GTiff"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print("Download concluído com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar os dados: {e}")
        exit()
else:
    print(f"O arquivo '{output_file}' já existe. Usando o arquivo local.")


# --- ETAPA 3 e 4: PROCESSAR E VISUALIZAR ---

try:
    with rasterio.open(output_file) as src:
        elevation = src.read(1)
        transform = src.transform
        
        elevation[elevation < -1000] = np.nan
        
        min_elev = np.nanmin(elevation)
        max_elev = np.nanmax(elevation)
        print(f"\nAnálise da elevação na área:")
        print(f"Elevação Mínima: {min_elev:.2f} metros")
        print(f"Elevação Máxima: {max_elev:.2f} metros")

        # 1. Visualização 2D do Modelo de Elevação
        fig, ax = plt.subplots(figsize=(10, 10))
        img_plot = show(elevation, ax=ax, transform=transform, cmap='terrain')
        ax.plot(ponto_central_lon, ponto_central_lat, 'r*', markersize=15, label='Ponto Central')
        ax.set_title('Modelo Digital de Elevação da Área')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend()
        cbar = fig.colorbar(img_plot.get_images()[0], ax=ax, shrink=0.7)
        cbar.set_label('Elevação (metros)')
        plt.show()

        # 2. ANÁLISE BÔNUS: PERFIL TOPOGRÁFICO
        print("\nGerando perfil topográfico...")
        num_pontos = 100
        linha_coords = np.zeros((num_pontos, 2))
        linha_coords[:, 0] = np.linspace(bounds[1], bounds[3], num_pontos)
        linha_coords[:, 1] = np.full(num_pontos, ponto_central_lat)
        elev_perfil = [val[0] for val in src.sample(linha_coords)]
        
        plt.figure(figsize=(12, 6))
        plt.plot(linha_coords[:, 0], elev_perfil, color='green')
        plt.title('Perfil Topográfico (Oeste-Leste)')
        plt.xlabel('Longitude')
        plt.ylabel('Elevação (metros)')
        plt.grid(True)
        plt.fill_between(linha_coords[:, 0], elev_perfil, color='green', alpha=0.2)
        plt.show()

except Exception as e:
    print(f"\nOcorreu um erro ao processar o arquivo de elevação: {e}")
    print("Verifique se o download foi bem-sucedido e se o arquivo não está corrompido.")