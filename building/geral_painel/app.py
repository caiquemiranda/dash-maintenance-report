import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(
    page_title="Visualização dos Painéis de Incêndio",
    layout="wide"
)

# Título da aplicação
st.title("Dados dos Painéis de Detecção de Incêndio")

# Leitura dos arquivos CSV
@st.cache_data
def carregar_dados(arquivo):
    return pd.read_csv(arquivo)

# Caminho para os arquivos
painel1 = "data/PN01.csv"
painel2 = "data/PN02.csv"

# Carregando os dados
df_painel1 = carregar_dados(painel1)
df_painel2 = carregar_dados(painel2)

# Criando duas colunas para exibir os painéis lado a lado
col1, col2 = st.columns(2)

with col1:
    st.subheader("Painel 1 (PN01)")
    st.dataframe(df_painel1, use_container_width=True)

with col2:
    st.subheader("Painel 2 (PN02)")
    st.dataframe(df_painel2, use_container_width=True)

# Adicionar informações sobre os dados
st.markdown("---")
st.subheader("Informações dos Dados")

col3, col4 = st.columns(2)

with col3:
    st.write("**Painel 1 (PN01)**")
    st.write(f"Total de registros: {len(df_painel1)}")
    st.write("Colunas disponíveis:")
    st.write(df_painel1.columns.tolist())

with col4:
    st.write("**Painel 2 (PN02)**")
    st.write(f"Total de registros: {len(df_painel2)}")
    st.write("Colunas disponíveis:")
    st.write(df_painel2.columns.tolist())
