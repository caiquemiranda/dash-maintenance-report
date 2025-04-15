import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Analisador de TroubleLog",
    layout="wide"
)

st.title("Analisador de Log de Problemas")

# Função para processar o arquivo de log
def processar_troublelog(conteudo):
    # Remover cabeçalhos de página
    conteudo = re.sub(r'-{80,}\nService Port\s+Page \d+\nReport 2 : Trouble Historical Log\s+\d+:\d+:\d+\s+\w+ \d+-\w+-\d+\n-{80,}', '', conteudo)
    
    # Dividir o conteúdo em linhas e remover linhas vazias
    linhas = [linha for linha in conteudo.split('\n') if linha.strip()]
    
    registros = []
    i = 0
    total_linhas = len(linhas)
    
    # Criar uma barra de progresso para arquivos grandes
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while i < total_linhas:
        # Atualizar progresso a cada 1000 linhas
        if i % 1000 == 0:
            progress = min(i / total_linhas, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Processando... {i}/{total_linhas} linhas ({int(progress*100)}%)")
        
        linha = linhas[i]
        
        # Verificar se a linha começa com "ENTRY"
        entry_match = re.match(r'ENTRY (\d+)\s+(\d+:\d+:\d+)\s+(\w+) (\d+-\w+-\d+) (.+?)$', linha)
        if entry_match:
            entry_num = entry_match.group(1).strip()
            hora = entry_match.group(2).strip()
            dia_semana = entry_match.group(3).strip()
            data = entry_match.group(4).strip()
            local = entry_match.group(5).strip()
            
            # Inicializar tipo_dispositivo e status
            tipo_dispositivo = ""
            status = ""
            
            # Verificar se há informações adicionais na próxima linha
            if i + 1 < total_linhas:
                proxima_linha = linhas[i + 1]
                # Se a próxima linha não começa com "ENTRY", assume que contém tipo_dispositivo e status
                if not proxima_linha.startswith("ENTRY"):
                    # Busca por dois blocos de texto separados por múltiplos espaços
                    info_match = re.search(r'^\s+(.+?)\s{2,}(.+?)$', proxima_linha)
                    if info_match:
                        tipo_dispositivo = info_match.group(1).strip()
                        status = info_match.group(2).strip()
                        i += 1  # Avança para a próxima linha, já que foi processada
            
            # Tratamento especial para entradas com "ACKNOWLEDGED"
            if "TROUBLES ACKNOWLEDGED" in local:
                if "AT MAIN PANEL" in local:
                    partes = local.split("AT MAIN PANEL")
                    local = "TROUBLES"
                    status = "ACKNOWLEDGED"
                    tipo_dispositivo = "AT MAIN PANEL"
            
            if "SUPERVISORIES ACKNOWLEDGED" in local:
                if "AT MAIN PANEL" in local:
                    partes = local.split("AT MAIN PANEL")
                    local = "SUPERVISORIES"
                    status = "ACKNOWLEDGED"
                    tipo_dispositivo = "AT MAIN PANEL"
            
            # Converter data para formato padrão
            try:
                data_obj = datetime.strptime(f"{dia_semana} {data}", "%a %d-%b-%y")
                data_formatada = data_obj.strftime("%d-%m-%Y")
                # Adicionar data como objeto datetime para facilitar a análise temporal
                data_datetime = data_obj
            except:
                data_formatada = data
                data_datetime = None
            
            # Extrair a hora como número para análise temporal
            try:
                hora_parts = hora.split(':')
                hora_numero = int(hora_parts[0])
            except:
                hora_numero = 0
            
            registros.append({
                "Entrada": entry_num,
                "Hora": hora,
                "Hora_Numero": hora_numero,
                "Data": data_formatada,
                "Data_Obj": data_datetime,
                "Dia da Semana": dia_semana,
                "Local": local,
                "Tipo de Dispositivo": tipo_dispositivo,
                "Status": status
            })
        
        i += 1
    
    # Completar a barra de progresso
    progress_bar.progress(1.0)
    status_text.text(f"Processamento concluído! {len(registros)} registros encontrados.")
    
    df = pd.DataFrame(registros)
    
    # Verificar se capturamos todos os registros esperados
    if len(registros) > 0:
        ultimo_registro = int(registros[-1]["Entrada"])
        st.sidebar.info(f"Registros processados: {len(registros)} / Último registro: #{ultimo_registro}")
        
        # Verificar se há registros ausentes
        entries = [int(r["Entrada"]) for r in registros]
        entries_set = set(entries)
        expected_entries = set(range(1, ultimo_registro + 1))
        missing_entries = expected_entries - entries_set
        if missing_entries:
            st.sidebar.warning(f"Registros ausentes: {len(missing_entries)}")
            st.sidebar.write(f"IDs ausentes: {sorted(list(missing_entries))[:10]}...")
    
    return df

# Função para criar análises visuais dos dados
def criar_visualizacoes(df):
    st.subheader("Análise Temporal")
    
    # Verificar se temos dados de data válidos
    if 'Data_Obj' in df.columns and not df['Data_Obj'].isnull().all():
        # Criar um dataframe agregado por data
        df_por_data = df.groupby('Data').size().reset_index(name='Contagem')
        
        # Ordenar por data para visualização cronológica
        if 'Data_Formatada' in df.columns and not df['Data_Formatada'].isnull().all():
            min_date = df['Data_Formatada'].min()
            max_date = df['Data_Formatada'].max()
        else:
            # Usar datas como estão se não pudermos converter
            min_date = None
            max_date = None
        
        # Criar seletores de data
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            modo_visualizacao = st.radio("Modo de visualização:", ["Todas as datas", "Período específico", "Dia específico"])
        
        if modo_visualizacao == "Período específico" and min_date and max_date:
            with col2:
                data_inicio = st.date_input("Data inicial", min_date)
                data_fim = st.date_input("Data final", max_date)
            
            # Filtrar dataframe por período
            df_filtrado = df[(df['Data_Formatada'] >= pd.to_datetime(data_inicio)) & 
                            (df['Data_Formatada'] <= pd.to_datetime(data_fim))]
            
            # Criar dataframe agregado por data
            df_periodo = df_filtrado.groupby('Data').size().reset_index(name='Contagem')
            
            # Gráfico de ocorrências por período
            fig = px.bar(df_periodo, x='Data', y='Contagem', 
                        title=f'Ocorrências de {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
                        labels={'Contagem': 'Número de Ocorrências', 'Data': 'Data'},
                        color='Contagem', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar estatísticas do período
            st.subheader(f"Estatísticas do Período ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})")
            total_ocorrencias = df_periodo['Contagem'].sum()
            media_ocorrencias = df_periodo['Contagem'].mean()
            max_ocorrencias = df_periodo['Contagem'].max()
            data_max_ocorrencias = df_periodo.loc[df_periodo['Contagem'].idxmax(), 'Data']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de ocorrências", total_ocorrencias)
            col2.metric("Média diária", f"{media_ocorrencias:.2f}")
            col3.metric("Maior ocorrência", f"{max_ocorrencias} ({data_max_ocorrencias})")
            
        elif modo_visualizacao == "Dia específico" and min_date and max_date:
            with col2:
                data_especifica = st.date_input("Selecione a data", max_date)
            
            # Filtrar dataframe para a data específica
            df_dia = df[df['Data_Formatada'].dt.date == data_especifica]
            
            # Verificar se há dados para a data selecionada
            if len(df_dia) > 0:
                # Análise por hora para o dia específico
                df_hora_dia = df_dia.groupby('Hora_Numero').size().reset_index(name='Contagem')
                
                # Gráfico de ocorrências por hora no dia específico
                fig_hora_dia = px.bar(df_hora_dia, x='Hora_Numero', y='Contagem',
                                    title=f'Ocorrências em {data_especifica.strftime("%d/%m/%Y")} por Hora',
                                    labels={'Contagem': 'Número de Ocorrências', 'Hora_Numero': 'Hora'},
                                    color='Contagem', color_continuous_scale='Viridis')
                fig_hora_dia.update_xaxes(tickvals=list(range(0, 24)))
                st.plotly_chart(fig_hora_dia, use_container_width=True)
                
                # Detalhamento por tipo de dispositivo nesse dia
                if 'Tipo de Dispositivo' in df.columns and not df['Tipo de Dispositivo'].empty:
                    st.subheader(f"Dispositivos com Problemas em {data_especifica.strftime('%d/%m/%Y')}")
                    df_dispositivos_dia = df_dia[df_dia['Tipo de Dispositivo'] != ''].groupby('Tipo de Dispositivo').size().reset_index(name='Contagem')
                    df_dispositivos_dia = df_dispositivos_dia.sort_values('Contagem', ascending=False)
                    
                    fig_disp_dia = px.bar(df_dispositivos_dia, y='Tipo de Dispositivo', x='Contagem',
                                        labels={'Contagem': 'Número de Ocorrências', 'Tipo de Dispositivo': 'Dispositivo'},
                                        color='Contagem', color_continuous_scale='Viridis',
                                        orientation='h')
                    st.plotly_chart(fig_disp_dia, use_container_width=True)
                
                # Detalhamento por status nesse dia
                if 'Status' in df.columns and not df['Status'].empty:
                    st.subheader(f"Status de Falha em {data_especifica.strftime('%d/%m/%Y')}")
                    df_status_dia = df_dia[df_dia['Status'] != ''].groupby('Status').size().reset_index(name='Contagem')
                    df_status_dia = df_status_dia.sort_values('Contagem', ascending=False)
                    
                    fig_status_dia = px.bar(df_status_dia, y='Status', x='Contagem',
                                            labels={'Contagem': 'Número de Ocorrências', 'Status': 'Status'},
                                            color='Contagem', color_continuous_scale='Viridis',
                                            orientation='h')
                    st.plotly_chart(fig_status_dia, use_container_width=True)
                
                # Tabela com todos os registros do dia
                st.subheader(f"Todos os Registros de {data_especifica.strftime('%d/%m/%Y')}")
                st.dataframe(df_dia.drop(columns=['Data_Formatada', 'Data_Obj', 'Hora_Numero', 'Dia_Ordem'], errors='ignore'), use_container_width=True)
            else:
                st.warning(f"Não há registros para a data {data_especifica.strftime('%d/%m/%Y')}")
        else:
            # Visualização de todas as datas
            # Calcular o número ideal de registros a mostrar baseado na quantidade de datas
            if len(df_por_data) > 50:
                st.info(f"O log contém {len(df_por_data)} datas diferentes. O gráfico mostra as ocorrências diárias, use os controles acima para filtrar períodos específicos.")
            
            # Gráfico de todas as ocorrências por data
            fig = px.bar(df_por_data, x='Data', y='Contagem', 
                        title='Ocorrências por Data (Todas as datas)',
                        labels={'Contagem': 'Número de Ocorrências', 'Data': 'Data'},
                        color='Contagem', color_continuous_scale='Viridis')
            
            if len(df_por_data) > 30:
                # Se houver muitas datas, ajustar o layout para melhor visualização
                fig.update_layout(xaxis={'categoryarray': df_por_data['Data'].tolist()})
                if len(df_por_data) > 50:
                    fig.update_layout(xaxis={'showticklabels': False})
                    fig.add_annotation(
                        text="Muitas datas para exibir os rótulos. Use o zoom ou filtros acima.",
                        xref="paper", yref="paper",
                        x=0.5, y=-0.15,
                        showarrow=False
                    )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Top 5 dias com mais ocorrências
        st.subheader("Dias com Maior Número de Ocorrências")
        top_dias = df_por_data.sort_values('Contagem', ascending=False).head(5)
        st.dataframe(top_dias, use_container_width=True)
    
    # Análise por hora do dia
    if 'Hora_Numero' in df.columns:
        st.subheader("Análise por Hora do Dia")
        df_por_hora = df.groupby('Hora_Numero').size().reset_index(name='Contagem')
        
        # Gráfico de ocorrências por hora
        fig_hora = px.bar(df_por_hora, x='Hora_Numero', y='Contagem',
                         title='Ocorrências por Hora do Dia',
                         labels={'Contagem': 'Número de Ocorrências', 'Hora_Numero': 'Hora'},
                         color='Contagem', color_continuous_scale='Viridis')
        fig_hora.update_xaxes(tickvals=list(range(0, 24)))
        st.plotly_chart(fig_hora, use_container_width=True)
    
    # Análise de locais específicos com mais problemas (descrição)
    st.subheader("Locais/Dispositivos Específicos com Mais Problemas")
    
    if 'Local' in df.columns:
        # Excluir entradas genéricas de reconhecimento
        df_locais = df[~df['Local'].isin(['TROUBLES', 'SUPERVISORIES', 'HARDWARE RESET IN PROGRESS'])]
        
        # Pegar os 15 locais mais problemáticos
        locais_contagem = df_locais.groupby('Local').size().reset_index(name='Contagem')
        locais_contagem = locais_contagem.sort_values('Contagem', ascending=False).head(15)
        
        # Gráfico de barras horizontais para locais
        fig_locais = px.bar(locais_contagem, y='Local', x='Contagem',
                          title='Top 15 Locais/Dispositivos com Mais Problemas',
                          labels={'Contagem': 'Número de Ocorrências', 'Local': 'Local/Dispositivo'},
                          color='Contagem', color_continuous_scale='Viridis',
                          orientation='h')
        st.plotly_chart(fig_locais, use_container_width=True)
        
        # Análise combinada: Local x Tipo de Dispositivo
        if 'Tipo de Dispositivo' in df.columns and not df['Tipo de Dispositivo'].empty:
            st.subheader("Análise por Local e Tipo de Dispositivo")
            df_local_tipo = df_locais.groupby(['Local', 'Tipo de Dispositivo']).size().reset_index(name='Contagem')
            df_local_tipo = df_local_tipo.sort_values('Contagem', ascending=False).head(15)
            
            fig_local_tipo = px.bar(df_local_tipo, 
                                   x='Contagem', 
                                   y='Local',
                                   color='Tipo de Dispositivo',
                                   title='Ocorrências por Local e Tipo de Dispositivo',
                                   labels={'Contagem': 'Número de Ocorrências', 'Local': 'Local/Dispositivo'},
                                   orientation='h')
            st.plotly_chart(fig_local_tipo, use_container_width=True)
        
        # Análise combinada: Local x Status
        if 'Status' in df.columns and not df['Status'].empty:
            st.subheader("Análise por Local e Status")
            df_local_status = df_locais.groupby(['Local', 'Status']).size().reset_index(name='Contagem')
            df_local_status = df_local_status.sort_values('Contagem', ascending=False).head(15)
            
            fig_local_status = px.bar(df_local_status, 
                                     x='Contagem', 
                                     y='Local',
                                     color='Status',
                                     title='Tipos de Problemas por Local',
                                     labels={'Contagem': 'Número de Ocorrências', 'Local': 'Local/Dispositivo'},
                                     orientation='h')
            st.plotly_chart(fig_local_status, use_container_width=True)
    
    # Análise de dispositivos mais problemáticos
    st.subheader("Dispositivos Mais Problemáticos")
    
    if 'Tipo de Dispositivo' in df.columns and not df['Tipo de Dispositivo'].empty:
        # Excluir dispositivos vazios
        df_dispositivos = df[df['Tipo de Dispositivo'] != '']
        
        # Top dispositivos com problemas
        dispositivos_contagem = df_dispositivos.groupby('Tipo de Dispositivo').size().reset_index(name='Contagem')
        dispositivos_contagem = dispositivos_contagem.sort_values('Contagem', ascending=False).head(10)
        
        # Gráfico de barras horizontais
        fig_disp = px.bar(dispositivos_contagem, y='Tipo de Dispositivo', x='Contagem',
                         title='Top 10 Dispositivos com Problemas',
                         labels={'Contagem': 'Número de Ocorrências', 'Tipo de Dispositivo': 'Dispositivo'},
                         color='Contagem', color_continuous_scale='Viridis',
                         orientation='h')
        st.plotly_chart(fig_disp, use_container_width=True)
    
    # Análise de status mais comuns
    st.subheader("Status de Falha Mais Comuns")
    
    if 'Status' in df.columns and not df['Status'].empty:
        # Excluir status vazios
        df_status = df[df['Status'] != '']
        
        # Top status
        status_contagem = df_status.groupby('Status').size().reset_index(name='Contagem')
        status_contagem = status_contagem.sort_values('Contagem', ascending=False).head(10)
        
        # Gráfico de barras horizontais
        fig_status = px.bar(status_contagem, y='Status', x='Contagem',
                           title='Top 10 Status de Falha',
                           labels={'Contagem': 'Número de Ocorrências', 'Status': 'Status'},
                           color='Contagem', color_continuous_scale='Viridis',
                           orientation='h')
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Mapa de calor de ocorrências por dia da semana e hora
    st.subheader("Mapa de Calor: Dia da Semana × Hora")
    
    if 'Dia da Semana' in df.columns and 'Hora_Numero' in df.columns:
        # Criar mapeamento para ordenar dias da semana
        dias_ordem = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
        
        # Criar coluna com ordem dos dias
        df['Dia_Ordem'] = df['Dia da Semana'].map(dias_ordem)
        
        # Agrupar por dia da semana e hora
        heatmap_data = df.groupby(['Dia da Semana', 'Hora_Numero']).size().reset_index(name='Contagem')
        
        # Criar uma matriz com todos os dias da semana e horas
        dias = list(dias_ordem.keys())
        horas = list(range(24))
        
        # Criar um pivot table para o mapa de calor
        pivot_data = heatmap_data.pivot_table(
            values='Contagem', 
            index='Dia da Semana', 
            columns='Hora_Numero', 
            fill_value=0
        ).reindex(dias)
        
        # Criar o mapa de calor
        fig_heatmap = px.imshow(
            pivot_data,
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Ocorrências"),
            x=horas,
            y=dias,
            color_continuous_scale="Viridis",
            title="Ocorrências por Dia da Semana e Hora"
        )
        
        fig_heatmap.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        st.plotly_chart(fig_heatmap, use_container_width=True)

# Botão de upload do arquivo
uploaded_file = st.file_uploader("Carregue o arquivo TroubleLog.txt", type=["txt"])

if uploaded_file is not None:
    # Exibir informações sobre o arquivo
    st.success(f"Arquivo carregado: {uploaded_file.name}")
    
    # Ler o conteúdo do arquivo
    conteudo = uploaded_file.getvalue().decode("utf-8", errors="replace")
    
    # Processar o conteúdo do arquivo
    try:
        df = processar_troublelog(conteudo)
        
        # Preparar o dataframe para análise
        if 'Data' in df.columns:
            df['Data_Formatada'] = pd.to_datetime(df['Data'], format='%d-%m-%Y', errors='coerce')
        
        # Configuração dos filtros na barra lateral
        st.sidebar.title("Filtros Globais")
        
        # Filtro de data
        if 'Data_Formatada' in df.columns and not df['Data_Formatada'].isnull().all():
            min_date = df['Data_Formatada'].min().date()
            max_date = df['Data_Formatada'].max().date()
            
            date_filter = st.sidebar.expander("Filtrar por Data", expanded=False)
            with date_filter:
                use_date_filter = st.checkbox("Ativar filtro de data")
                
                if use_date_filter:
                    date_range = st.date_input(
                        "Selecione o período:",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_range) == 2:
                        start_date, end_date = date_range
                        df = df[(df['Data_Formatada'].dt.date >= start_date) & 
                                (df['Data_Formatada'].dt.date <= end_date)]
        
        # Filtro de local
        if 'Local' in df.columns and not df['Local'].empty:
            local_filter = st.sidebar.expander("Filtrar por Local", expanded=False)
            with local_filter:
                use_local_filter = st.checkbox("Ativar filtro de local")
                
                if use_local_filter:
                    locais = ["Todos"] + sorted(df['Local'].unique().tolist())
                    local_selecionado = st.selectbox("Selecione o local:", locais)
                    
                    if local_selecionado != "Todos":
                        df = df[df['Local'] == local_selecionado]
        
        # Filtro de tipo de dispositivo
        if 'Tipo de Dispositivo' in df.columns and not df['Tipo de Dispositivo'].empty:
            device_filter = st.sidebar.expander("Filtrar por Dispositivo", expanded=False)
            with device_filter:
                use_device_filter = st.checkbox("Ativar filtro de dispositivo")
                
                if use_device_filter:
                    dispositivos = ["Todos"] + sorted(df['Tipo de Dispositivo'].unique().tolist())
                    dispositivo_selecionado = st.selectbox("Selecione o dispositivo:", dispositivos)
                    
                    if dispositivo_selecionado != "Todos":
                        df = df[df['Tipo de Dispositivo'] == dispositivo_selecionado]
        
        # Filtro de status
        if 'Status' in df.columns and not df['Status'].empty:
            status_filter = st.sidebar.expander("Filtrar por Status", expanded=False)
            with status_filter:
                use_status_filter = st.checkbox("Ativar filtro de status")
                
                if use_status_filter:
                    status_list = ["Todos"] + sorted(df['Status'].unique().tolist())
                    status_selecionado = st.selectbox("Selecione o status:", status_list)
                    
                    if status_selecionado != "Todos":
                        df = df[df['Status'] == status_selecionado]
        
        # Exibir informações sobre os dados filtrados
        total_registros = len(df)
        st.sidebar.metric("Registros filtrados", total_registros)
        
        # Exibir resumo dos dados filtrados
        st.subheader("Resumo dos Logs de Problemas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de registros", total_registros)
        with col2:
            if 'Local' in df.columns:
                st.metric("Locais únicos", df['Local'].nunique())
        with col3:
            if 'Status' in df.columns:
                st.metric("Status diferentes", df['Status'].nunique())
        
        # Criar abas para navegação
        tab1, tab2, tab3 = st.tabs(["Dados", "Visualizações", "Estatísticas"])
        
        with tab1:
            # Exibir tabela com os dados
            st.subheader("Tabela de Logs")
            # Remover colunas auxiliares usadas apenas para análise
            display_df = df.drop(columns=['Hora_Numero', 'Data_Obj', 'Dia_Ordem', 'Data_Formatada'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)
            
            # Opção para download dos dados processados
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download dos dados em CSV",
                data=csv,
                file_name="troublelog_processado.csv",
                mime="text/csv"
            )
        
        with tab2:
            # Criar visualizações dos dados
            criar_visualizacoes(df)
            
        with tab3:
            # Análise estatística básica
            st.subheader("Estatísticas")
            subtab1, subtab2, subtab3 = st.tabs(["Locais", "Status", "Dispositivos"])
            
            with subtab1:
                if 'Local' in df.columns and not df['Local'].empty:
                    st.subheader("Ocorrências por Local")
                    local_counts = df['Local'].value_counts().reset_index()
                    local_counts.columns = ['Local', 'Contagem']
                    st.dataframe(local_counts, use_container_width=True)
            
            with subtab2:
                if 'Status' in df.columns and not df['Status'].empty:
                    st.subheader("Ocorrências por Status")
                    status_counts = df['Status'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Contagem']
                    st.dataframe(status_counts, use_container_width=True)
                    
            with subtab3:
                if 'Tipo de Dispositivo' in df.columns and not df['Tipo de Dispositivo'].empty:
                    st.subheader("Ocorrências por Tipo de Dispositivo")
                    device_counts = df['Tipo de Dispositivo'].value_counts().reset_index()
                    device_counts.columns = ['Tipo de Dispositivo', 'Contagem']
                    st.dataframe(device_counts, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
else:
    # Exibir instruções quando nenhum arquivo estiver carregado
    st.info("Por favor, carregue um arquivo TroubleLog.txt para análise.")
    
    # Exemplo de como os dados serão exibidos
    st.subheader("Formato de Saída")
    exemplo = pd.DataFrame({
        "Entrada": ["1", "2", "3", "10"],
        "Hora": ["4:12:32", "4:17:08", "4:46:00", "16:48:02"],
        "Data": ["15-01-2025", "15-01-2025", "15-01-2025", "15-01-2025"],
        "Dia da Semana": ["WED", "WED", "WED", "WED"],
        "Local": ["DF - FUNDO LOJA CHAME PIZZA L2 M3-57", "TROUBLES", "BOMBA JOCKEY ACIONADA", "DF - FUNDO LOJA CHAME PIZZA L2 M3-57"],
        "Tipo de Dispositivo": ["SMOKE DETECTOR", "AT MAIN PANEL", "SUPERVISORY MONITOR", "SMOKE DETECTOR"],
        "Status": ["EXCESSIVELY DIRTY", "ACKNOWLEDGED", "ABNORMAL", "HEAD MISSING"]
    })
    st.dataframe(exemplo, use_container_width=True)
