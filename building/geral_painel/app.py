import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# Exibindo informações sobre as colunas
st.write("### Estrutura dos Dados")
st.write("Colunas do Painel 1:")
st.write(df_painel1.columns.tolist())
st.write("\nPrimeiras linhas do Painel 1:")
st.write(df_painel1.head())

st.write("\nColunas do Painel 2:")
st.write(df_painel2.columns.tolist())
st.write("\nPrimeiras linhas do Painel 2:")
st.write(df_painel2.head())

# Função para análise de dispositivos por laço
def analisar_lacos(df, nome_painel):
    # Contagem de dispositivos por laço (MAP)
    devices_por_laco = df[df['CUSTOM_LABEL'] != 'UNUSED']['MAP'].value_counts().sort_index()
    
    # Percentual de utilização por laço
    percentual_uso = (devices_por_laco / 250 * 100).round(2)
    
    # Criar gráfico de barras para dispositivos por laço
    fig_devices = go.Figure()
    fig_devices.add_trace(go.Bar(
        x=devices_por_laco.index,
        y=devices_por_laco.values,
        name='Dispositivos',
        text=devices_por_laco.values,
        textposition='auto',
    ))
    fig_devices.update_layout(
        title=f'Quantidade de Dispositivos por Laço - {nome_painel}',
        xaxis_title='Número do Laço',
        yaxis_title='Quantidade de Dispositivos',
        showlegend=False
    )
    
    # Criar gráfico de gauge para cada laço
    gauges = []
    for laco in devices_por_laco.index:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=percentual_uso[laco],
            title={'text': f'Laço {laco}'},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "gray"},
                    {'range': [75, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        gauge.update_layout(height=200)
        gauges.append(gauge)
    
    return fig_devices, gauges, devices_por_laco, percentual_uso

# Análise dos dados
st.header("Análise dos Painéis")

# Análise Painel 1
st.subheader("Painel 1 (PN01)")
fig_devices1, gauges1, devices1, percentual1 = analisar_lacos(df_painel1, "Painel 1")
st.plotly_chart(fig_devices1, use_container_width=True)

# Métricas do Painel 1
col_metricas1 = st.columns(len(gauges1))
for idx, (gauge, col) in enumerate(zip(gauges1, col_metricas1)):
    with col:
        st.plotly_chart(gauge, use_container_width=True)
        st.metric(
            f"Laço {devices1.index[idx]}",
            f"{devices1.values[idx]} dispositivos",
            f"{percentual1.values[idx]:.1f}% utilizado"
        )

# Análise Painel 2
st.subheader("Painel 2 (PN02)")
fig_devices2, gauges2, devices2, percentual2 = analisar_lacos(df_painel2, "Painel 2")
st.plotly_chart(fig_devices2, use_container_width=True)

# Métricas do Painel 2
col_metricas2 = st.columns(len(gauges2))
for idx, (gauge, col) in enumerate(zip(gauges2, col_metricas2)):
    with col:
        st.plotly_chart(gauge, use_container_width=True)
        st.metric(
            f"Laço {devices2.index[idx]}",
            f"{devices2.values[idx]} dispositivos",
            f"{percentual2.values[idx]:.1f}% utilizado"
        )

# Tabelas de dados originais
st.header("Dados Detalhados dos Painéis")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Painel 1 (PN01)")
    st.dataframe(df_painel1, use_container_width=True)

with col2:
    st.subheader("Painel 2 (PN02)")
    st.dataframe(df_painel2, use_container_width=True)

# Informações adicionais
st.markdown("---")
st.subheader("Informações dos Dados")

col3, col4 = st.columns(2)

with col3:
    st.write("**Painel 1 (PN01)**")
    total_devices1 = len(df_painel1[df_painel1['CUSTOM_LABEL'] != 'UNUSED'])
    st.write(f"Total de dispositivos ativos: {total_devices1}")
    st.write(f"Total de endereços não utilizados: {len(df_painel1[df_painel1['CUSTOM_LABEL'] == 'UNUSED'])}")
    st.write("Distribuição por laço:")
    st.write(devices1)

with col4:
    st.write("**Painel 2 (PN02)**")
    total_devices2 = len(df_painel2[df_painel2['CUSTOM_LABEL'] != 'UNUSED'])
    st.write(f"Total de dispositivos ativos: {total_devices2}")
    st.write(f"Total de endereços não utilizados: {len(df_painel2[df_painel2['CUSTOM_LABEL'] == 'UNUSED'])}")
    st.write("Distribuição por laço:")
    st.write(devices2)
