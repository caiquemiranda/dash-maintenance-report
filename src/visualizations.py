import plotly.express as px
import pandas as pd
import streamlit as st

def criar_grafico_dispositivos(df):
    """Cria gráfico de contagem por tipo de dispositivo"""
    device_count = df['DEVICE_TYPE'].value_counts().reset_index()
    device_count.columns = ['Tipo de Dispositivo', 'Contagem']
    
    fig = px.bar(device_count, x='Tipo de Dispositivo', y='Contagem',
                title='Quantidade por Tipo de Dispositivo',
                color='Contagem', height=400)
    return fig

def criar_grafico_status(df):
    """Cria gráfico de contagem por status"""
    status_count = df['STATUS'].value_counts().reset_index()
    status_count.columns = ['Status', 'Contagem']
    
    fig = px.bar(status_count, x='Status', y='Contagem',
               title='Quantidade por Status',
               color='Contagem', height=400)
    return fig

def criar_grafico_node(df):
    """Cria gráfico de contagem por NODE"""
    node_count = df['NODE'].value_counts().reset_index()
    node_count.columns = ['NODE', 'Contagem']
    
    fig = px.bar(node_count, x='NODE', y='Contagem',
                title='Quantidade por NODE',
                color='Contagem', height=400)
    return fig

def criar_grafico_top_falhas(df):
    """Cria gráfico com as 10 falhas mais frequentes"""
    # Agrupar por POINT_NAME, DESCRIPTION, DEVICE_TYPE e STATUS
    top_falhas = df.groupby(['POINT_NAME', 'DESCRIPTION', 'DEVICE_TYPE', 'STATUS']).size().reset_index(name='Contagem')
    top_falhas = top_falhas.sort_values('Contagem', ascending=False).head(10)
    

    top_falhas['Descrição Falha'] = top_falhas.apply(
        lambda x: f"{x['POINT_NAME']} - {x['DESCRIPTION']} ({x['DEVICE_TYPE']}): {x['STATUS']}", axis=1
    )
    
    fig = px.bar(top_falhas, x='Descrição Falha', y='Contagem',
                title='Top 10 Falhas Mais Frequentes',
                color='Contagem', height=500)
    fig.update_layout(xaxis_tickangle=-45)
    
    return fig, top_falhas
