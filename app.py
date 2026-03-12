import streamlit as st
import leafmap.foliumap as leafmap
from pystac_client import Client
import planetary_computer as pc
import pandas as pd

# 1. Configuração da Página
st.set_page_config(layout="wide", page_title="5A - Portal de Carbono")

# Estilo CSS para melhorar o visual das métricas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 25px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 Sistema de Monitoramento de Projetos de Carbono")
st.markdown("---")

# 2. Simulação de Banco de Dados (Pode ser substituído por pd.read_csv('seu_arquivo.csv'))
projects_db = {
    "5A-001": {
        "nome": "Fazenda Rio Novo - RS",
        "area_ha": 1250.5,
        "estoque_carbono": 45000,
        "ano_certificacao": 2017,
        "lat": -27.35, "lon": -53.39,
        "bbox": [-53.42, -27.38, -53.36, -27.32]
    },
    "5A-002": {
        "nome": "Reserva Mata Verde - SC",
        "area_ha": 890.2,
        "estoque_carbono": 32100,
        "ano_certificacao": 2015,
        "lat": -26.50, "lon": -49.20,
        "bbox": [-49.25, -26.55, -49.15, -26.45]
    }
}

# 3. Barra Lateral (Sidebar)
st.sidebar.image("https://5aeng.com.br/wp-content/uploads/2023/06/Logo-5A-Engenharia.png", width=150) # Logo fictícia
st.sidebar.header("Painel de Controle")

project_id = st.sidebar.selectbox("Selecione o Número do Projeto:", options=list(projects_db.keys()))
data = projects_db[project_id]

st.sidebar.markdown("---")
st.sidebar.subheader("Informações do Imóvel")
st.sidebar.write(f"**Proprietário:** {data['nome']}")
st.sidebar.write(f"**Ano Inicial:** {data['ano_certificacao']}")

# 4. Dashboard de Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Área Total", f"{data['area_ha']} ha")
col2.metric("Carbono (tCO2e)", f"{data['estoque_carbono']}")
col3.metric("Status", "Certificado")
col4.metric("Monitoramento", "Ativo")

# 5. Lógica de Acesso às Imagens de Satélite (STAC)
catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=pc.sign_inplace
)

def get_best_image(bbox, start_year, end_year):
    """Busca a imagem mais recente com menos nuvens em um intervalo de tempo"""
    date_range = f"{start_year}-01-01/{end_year}-12-31"
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=date_range,
        max_items=1,
        sortby=[{"field": "properties.datetime", "direction": "desc"}],
        query={"eo:cloud_cover": {"lt": 10}}
    )
    items = list(search.items())
    return items[0] if items else None

# Busca imagem de 10 anos atrás (ou ano de certificação) e imagem atual
item_passado = get_best_image(data["bbox"], data["ano_certificacao"], data["ano_certificacao"])
item_atual = get_best_image(data["bbox"], 2024, 2026)

# 6. Renderização do Mapa
st.subheader(f"Análise de Mudança de Uso do Solo ({data['ano_certificacao']} vs Atual)")

if item_passado and item_atual:
    m = leafmap.Map(center=[data['lat'], data['lon']], zoom=14)
    
    # Camada Histórica (Esquerda)
    left_layer = leafmap.stac_tile(
        collection="sentinel-2-l2a",
        item=item_passado.id, # Correção do ID
        assets=["visual"],
        titiler_endpoint="planetary-computer"
    )
    
    # Camada Atual (Direita)
    right_layer = leafmap.stac_tile(
        collection="sentinel-2-l2a",
        item=item_atual.id, # Correção do ID
        assets=["visual"],
        titiler_endpoint="planetary-computer"
    )
    
    # Criar Mapa Comparativo
    m.split_map(left_layer=left_layer, right_layer=right_layer)
    
    # --- ESPAÇO PARA POLÍGONOS GEOJSON ---
    # Se você tiver um arquivo .geojson com o limite da fazenda:
    # m.add_geojson("caminho_do_arquivo.geojson", layer_name="Limite da Área")
    
    st.info(f"📅 Comparando imagem de {item_passado.datetime.date()} com {item_atual.datetime.date()}")
    m.to_streamlit(height=650)
else:
    st.error("Erro ao carregar imagens de satélite para os períodos selecionados.")

st.markdown("---")
st.caption("© 2026 5A Inteligência e Engenharia - Portal de Transparência de Carbono")