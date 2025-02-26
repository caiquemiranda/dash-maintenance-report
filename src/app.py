#app.py

import streamlit as st
import pandas as pd
import datetime
import numpy as np
import os
import sys

# Adicionar o diretório pai ao path para encontrar os módulos independentemente 
# de como o script é executado
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar módulos com importações absolutas
import src.utils as utils
import src.parser as parser
import src.visualizations as viz
import src.device_analysis as device_analysis

def main():
    st.set_page_config(page_title="Processador de Logs TSW", page_icon="📊", layout="wide")
    st.title('Processador de Logs TSW')
    
    # Upload do arquivo
    arquivo = st.file_uploader("Faça upload do arquivo de log .txt", type=['txt'])
    
    if arquivo is not None:
        try:
            # Tentar decodificar o arquivo com diferentes codificações
            conteudo = utils.tentar_decodificar(arquivo)
            
            # Processar o arquivo e criar DataFrame
            df = parser.processar_arquivo(conteudo)
            
            # Adicionar filtros na barra lateral
            st.sidebar.header("Filtros")
            
            # Extrair valores únicos para filtros
            nodes_disponiveis = sorted(df['NODE'].dropna().unique().tolist())
            todos_status = sorted(df['STATUS'].dropna().unique().tolist())
            todos_devices = sorted(df['DEVICE_TYPE'].dropna().unique().tolist())
            todos_dispositivos = sorted(df['POINT_NAME'].dropna().unique().tolist())
            
            # Extrair datas para os filtros de período
            df['DATA_COMPLETA'] = pd.to_datetime(df['DATE_OBJ'])
            
            # Corrigir o problema com as datas
            if not df['DATA_COMPLETA'].empty and not df['DATA_COMPLETA'].isna().all():
                # Converter para lista de timestamps e usar min/max do Python
                datas_validas = [d for d in df['DATA_COMPLETA'] if pd.notna(d)]
                
                if datas_validas:
                    data_min = min(datas_validas).date()
                    data_max = max(datas_validas).date()
                    
                    # Filtro de período
                    st.sidebar.subheader("Período de Datas")
                    data_inicio = st.sidebar.date_input("Data Inicial", data_min, min_value=data_min, max_value=data_max)
                    data_fim = st.sidebar.date_input("Data Final", data_max, min_value=data_min, max_value=data_max)
                    
                    # Garantir que a data final não seja anterior à data inicial
                    if data_fim < data_inicio:
                        st.sidebar.error("Data final deve ser posterior à data inicial!")
                        data_fim = data_inicio
                else:
                    # Caso não existam datas válidas
                    data_hoje = datetime.date.today()
                    data_inicio = data_hoje
                    data_fim = data_hoje
            else:
                # Caso não existam datas válidas
                data_hoje = datetime.date.today()
                data_inicio = data_hoje
                data_fim = data_hoje
            
            # Filtros de NODE, DEVICE_TYPE e STATUS
            node_selecionado = st.sidebar.selectbox("NODE", ["Todos"] + nodes_disponiveis)
            
            device_types_selecionados = st.sidebar.multiselect(
                "Tipos de Dispositivo (múltipla escolha)",
                options=todos_devices,
                default=[]
            )
            
            status_selecionados = st.sidebar.multiselect(
                "Status (múltipla escolha)",
                options=todos_status,
                default=[]
            )
            
            # Novo filtro para análise de dispositivo específico
            st.sidebar.subheader("Análise de Dispositivo Específico")
            dispositivo_selecionado = st.sidebar.selectbox(
                "Selecione um dispositivo (POINT_NAME) para análise detalhada",
                ["Nenhum"] + todos_dispositivos
            )
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            # Filtro de período
            df_filtrado = df_filtrado[
                (df_filtrado['DATA_COMPLETA'].dt.date >= data_inicio) & 
                (df_filtrado['DATA_COMPLETA'].dt.date <= data_fim)
            ]
            
            # Filtro de NODE
            if node_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['NODE'] == node_selecionado]
            
            # Filtro de Tipo de Dispositivo (multiselect)
            if device_types_selecionados:
                df_filtrado = df_filtrado[df_filtrado['DEVICE_TYPE'].isin(device_types_selecionados)]
            
            # Filtro de Status (multiselect)
            if status_selecionados:
                df_filtrado = df_filtrado[df_filtrado['STATUS'].isin(status_selecionados)]
            
            # Exibir os dados originais
            with st.expander("Ver conteúdo original"):
                st.text(conteudo)
            
            # Exibir a tabela processada
            st.subheader('Dados Processados')
            st.dataframe(df_filtrado.drop(columns=['DATE_OBJ', 'DATA_COMPLETA']), use_container_width=True)
            
            # Adicionar algumas métricas
            st.subheader('Métricas')
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Registros", len(df_filtrado))
            with col2:
                bad_answers = len(df_filtrado[df_filtrado['STATUS'].str.contains('BAD ANSWER', na=False)])
                st.metric("Bad Answers", bad_answers)
            with col3:
                short_circuits = len(df_filtrado[df_filtrado['STATUS'].str.contains('SHORT CIRCUIT', na=False)])
                st.metric("Short Circuit", short_circuits)
            with col4:
                on_off_count = len(df_filtrado[df_filtrado['STATUS'].isin(['ON', 'OFF'])])
                st.metric("ON/OFF Switches", on_off_count)
            
            # Visualizações padrão
            col_esq, col_dir = st.columns(2)
            
            with col_esq:
                # Gráfico de contagem por tipo de dispositivo
                st.subheader('Contagem por Tipo de Dispositivo')
                fig_device = viz.criar_grafico_dispositivos(df_filtrado)
                st.plotly_chart(fig_device, use_container_width=True)
            
            with col_dir:
                # Gráfico de contagem por status
                st.subheader('Contagem por Status')
                fig_status = viz.criar_grafico_status(df_filtrado)
                st.plotly_chart(fig_status, use_container_width=True)
            
            # Gráfico de contagem por NODE
            st.subheader('Contagem por NODE')
            fig_node = viz.criar_grafico_node(df_filtrado)
            st.plotly_chart(fig_node, use_container_width=True)
            
            # Top 10 falhas mais comuns
            st.subheader('Top 10 Falhas Mais Frequentes')
            fig_top_falhas, top_falhas = viz.criar_grafico_top_falhas(df_filtrado)
            st.plotly_chart(fig_top_falhas, use_container_width=True)
            
            # Tabela com as top 10 falhas
            st.subheader('Detalhes das Top 10 Falhas')
            st.dataframe(top_falhas[['POINT_NAME', 'DESCRIPTION', 'DEVICE_TYPE', 'STATUS', 'Contagem']], use_container_width=True)
            
            # Análise de dispositivo específico
            if dispositivo_selecionado != "Nenhum":
                st.header(f'Análise do Dispositivo: {dispositivo_selecionado}')
                device_analysis.analisar_dispositivo(df, dispositivo_selecionado)
            
            # Botão para download dos dados processados
            csv = df_filtrado.drop(columns=['DATE_OBJ', 'DATA_COMPLETA']).to_csv(index=False, encoding='utf-8-sig', sep=';')
            st.download_button(
                label="Download dados processados (CSV)",
                data=csv,
                file_name="dados_processados.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f'Erro ao processar o arquivo: {str(e)}')

if __name__ == '__main__':
    main()

