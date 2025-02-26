#app.py

import streamlit as st
import re
import pandas as pd
import datetime
import plotly.express as px

def tentar_decodificar(arquivo):
    """Tenta decodificar o arquivo com diferentes codificações"""
    codificacoes = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for codec in codificacoes:
        try:
            return arquivo.getvalue().decode(codec)
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError("Não foi possível decodificar o arquivo com nenhuma das codificações conhecidas")

def processar_arquivo(conteudo):
    # Dividir o conteúdo em linhas
    linhas = conteudo.split('\n')
    
    # Pular as primeiras 6 linhas de cabeçalho
    linhas = linhas[6:]
    
    # Lista para armazenar os dados processados
    dados = []
    
    # Processar as linhas
    i = 0
    while i < len(linhas):
        # Pular linhas vazias
        if not linhas[i].strip():
            i += 1
            continue
            
        try:
            # Verificar se a linha começa com um ID e horário
            linha1_match = re.match(r'^\s*(\d+)\s+(\d{2}:\d{2}:\d{2})', linhas[i])
            if linha1_match:
                id_registro = linha1_match.group(1)
                horario = linha1_match.group(2)
                
                # Inicializar o registro com valores padrão
                registro = {
                    'ID': id_registro,
                    'TIME': horario,
                    'POINT_NAME': 'N/A',
                    'DESCRIPTION': 'N/A',
                    'DATE': 'N/A',
                    'NODE': 'N/A',
                    'DEVICE_TYPE': 'N/A',
                    'STATUS': 'N/A'
                }
                
                # Extrair POINT_NAME e DESCRIPTION
                linha_resto = linhas[i][len(id_registro):].strip()
                linha_resto = linha_resto[8:].strip()  # Remover o horário (8 caracteres: HH:MM:SS)
                
                if linha_resto:
                    # Tentar extrair o POINT_NAME
                    point_match = re.match(r'([\d:][^\ ]+)', linha_resto)
                    if point_match:
                        registro['POINT_NAME'] = point_match.group(1)
                        description = linha_resto[len(point_match.group(1)):].strip()
                        registro['DESCRIPTION'] = description
                    else:
                        # Se não conseguir extrair um POINT_NAME, considerar tudo como DESCRIPTION
                        registro['DESCRIPTION'] = linha_resto
                
                # Verificar se existem mais linhas para este registro
                linhas_registro = [linhas[i]]
                j = i + 1
                linha_data_encontrada = False
                linha_device_encontrada = False
                
                # Coletar todas as linhas do registro atual até encontrar o próximo registro ou fim do arquivo
                while j < len(linhas):
                    linha_atual = linhas[j].strip()
                    
                    # Se a linha começar com um número, é o início do próximo registro
                    if re.match(r'^\s*\d+\s+\d{2}:\d{2}:\d{2}', linhas[j]):
                        break
                    
                    if linha_atual:
                        linhas_registro.append(linhas[j])
                        
                        # Verificar se é uma linha com DATA e NODE
                        data_match = re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN)\s+(\d{2})-(\w{3})-(\d{2})', linha_atual)
                        node_match = re.search(r'\(NODE\s+(\d+)\)', linha_atual)
                        
                        if data_match and not linha_data_encontrada:
                            linha_data_encontrada = True
                            dia_semana = data_match.group(1)
                            dia = data_match.group(2)
                            mes_abrev = data_match.group(3)
                            ano = data_match.group(4)
                            
                            # Converter o mês de abreviação para número
                            meses = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
                                    'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
                            mes = meses.get(mes_abrev, '01')
                            
                            # Formatar a data como DD/MM/YYYY
                            registro['DATE'] = f"{dia}/{mes}/20{ano}"
                        
                        if node_match:
                            registro['NODE'] = node_match.group(1)
                        
                        # Verificar se é uma linha com DEVICE_TYPE e STATUS
                        if not linha_device_encontrada and not data_match:
                            # Se a linha não contém data e não está vazia, pode ser a linha de device/status
                            device_types = [
                                'SMOKE DETECTOR', 'Quick Alert Signal', 'AUXILIARY RELAY', 'PULL STATION',
                                'SUPERVISORY MONITOR', 'SIGNAL CIRCUIT', 'MAPNET ISOLATOR', 'FIRE MONITOR ZONE',
                                'TROUBLE RELAY'  # Adicionado para o novo caso
                            ]
                            
                            for device in device_types:
                                if device in linha_atual:
                                    linha_device_encontrada = True
                                    registro['DEVICE_TYPE'] = device
                                    
                                    # Extrair STATUS - tudo que vem depois do DEVICE_TYPE
                                    status_part = linha_atual[linha_atual.find(device) + len(device):].strip()
                                    if status_part:
                                        registro['STATUS'] = status_part
                                    break
                            
                            # Caso especial para linhas que não contêm um DEVICE_TYPE conhecido
                            if not linha_device_encontrada and 'TROUBLE GLOBAL' in linha_atual:
                                registro['DEVICE_TYPE'] = 'TROUBLE GLOBAL'
                                if 'ACKNOWLEDGE' in linha_atual:
                                    registro['STATUS'] = 'ACKNOWLEDGE'
                    
                    j += 1
                
                # Atualizar a descrição com linhas adicionais se necessário
                if len(linhas_registro) > 1 and 'DESCRIPTION' in registro:
                    # Verificar se há linhas de continuação da descrição
                    descricao_completa = registro['DESCRIPTION']
                    
                    # Para o caso específico de TROUBLE RELAY, concatenar a segunda linha à descrição
                    segunda_linha = linhas_registro[1].strip() if len(linhas_registro) > 1 else ""
                    if segunda_linha and not re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN)', segunda_linha) and not any(device in segunda_linha for device in device_types):
                        if descricao_completa != 'N/A':
                            descricao_completa += " " + segunda_linha
                        else:
                            descricao_completa = segunda_linha
                    
                    registro['DESCRIPTION'] = descricao_completa
                
                dados.append(registro)
                i = j  # Avançar para o próximo registro
            else:
                i += 1
        except Exception as e:
            print(f"Erro ao processar linha {i}: {str(e)}")
            i += 1
    
    # Criar DataFrame com as colunas na ordem especificada
    colunas = ['ID', 'TIME', 'POINT_NAME', 'DESCRIPTION', 'DATE', 'NODE', 'DEVICE_TYPE', 'STATUS']
    df = pd.DataFrame(dados)
    
    # Garantir que todas as colunas existam
    for coluna in colunas:
        if coluna not in df.columns:
            df[coluna] = 'N/A'
    
    # Converter a coluna de data para datetime
    df['DATE_OBJ'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y', errors='coerce')
    
    return df[colunas + ['DATE_OBJ']]

def main():
    st.title('Processador de Logs TSW')
    
    # Upload do arquivo
    arquivo = st.file_uploader("Faça upload do arquivo de log .txt", type=['txt'])
    
    if arquivo is not None:
        try:
            # Tentar decodificar o arquivo com diferentes codificações
            conteudo = tentar_decodificar(arquivo)
            
            # Processar o arquivo e criar DataFrame
            df = processar_arquivo(conteudo)
            
            # Adicionar filtros de data
            st.sidebar.header("Filtros")
            
            # Extrair datas únicas
            df['DIA'] = pd.to_datetime(df['DATE_OBJ']).dt.day
            df['MES'] = pd.to_datetime(df['DATE_OBJ']).dt.month
            df['ANO'] = pd.to_datetime(df['DATE_OBJ']).dt.year
            
            # Lista de dias, meses e anos disponíveis
            dias_disponiveis = sorted(df['DIA'].dropna().unique().tolist())
            meses_disponiveis = sorted(df['MES'].dropna().unique().tolist())
            anos_disponiveis = sorted(df['ANO'].dropna().unique().tolist())
            
            # Criar filtros
            dia_selecionado = st.sidebar.selectbox("Dia", ["Todos"] + dias_disponiveis)
            mes_selecionado = st.sidebar.selectbox("Mês", ["Todos"] + meses_disponiveis)
            ano_selecionado = st.sidebar.selectbox("Ano", ["Todos"] + anos_disponiveis)
            
            # Filtro de STATUS
            todos_status = sorted(df['STATUS'].unique().tolist())
            status_selecionado = st.sidebar.selectbox("Status", ["Todos"] + todos_status)
            
            # Filtro de DEVICE_TYPE
            todos_devices = sorted(df['DEVICE_TYPE'].unique().tolist())
            device_selecionado = st.sidebar.selectbox("Tipo de Dispositivo", ["Todos"] + todos_devices)
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            if dia_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['DIA'] == dia_selecionado]
            
            if mes_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['MES'] == mes_selecionado]
                
            if ano_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['ANO'] == ano_selecionado]
                
            if status_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['STATUS'] == status_selecionado]
                
            if device_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['DEVICE_TYPE'] == device_selecionado]
            
            # Exibir os dados originais
            with st.expander("Ver conteúdo original"):
                st.text(conteudo)
            
            # Exibir a tabela processada
            st.subheader('Dados Processados')
            st.dataframe(df_filtrado.drop(columns=['DATE_OBJ', 'DIA', 'MES', 'ANO']), use_container_width=True)
            
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
            
            # Gráfico de contagem por tipo de dispositivo
            st.subheader('Contagem por Tipo de Dispositivo')
            device_count = df_filtrado['DEVICE_TYPE'].value_counts().reset_index()
            device_count.columns = ['Tipo de Dispositivo', 'Contagem']
            
            fig_device = px.bar(device_count, x='Tipo de Dispositivo', y='Contagem',
                               title='Quantidade por Tipo de Dispositivo',
                               color='Contagem', height=400)
            st.plotly_chart(fig_device, use_container_width=True)
            
            # Gráfico de contagem por status
            st.subheader('Contagem por Status')
            status_count = df_filtrado['STATUS'].value_counts().reset_index()
            status_count.columns = ['Status', 'Contagem']
            
            fig_status = px.bar(status_count, x='Status', y='Contagem',
                               title='Quantidade por Status',
                               color='Contagem', height=400)
            st.plotly_chart(fig_status, use_container_width=True)
            
            # Top 10 falhas mais comuns
            st.subheader('Top 10 Falhas Mais Frequentes')
            
            # Agrupar por POINT_NAME, DESCRIPTION, DEVICE_TYPE e STATUS
            top_falhas = df_filtrado.groupby(['POINT_NAME', 'DESCRIPTION', 'DEVICE_TYPE', 'STATUS']).size().reset_index(name='Contagem')
            top_falhas = top_falhas.sort_values('Contagem', ascending=False).head(10)
            
            # Criar uma coluna de descrição mais amigável
            top_falhas['Descrição Falha'] = top_falhas.apply(
                lambda x: f"{x['POINT_NAME']} - {x['DESCRIPTION']} ({x['DEVICE_TYPE']}): {x['STATUS']}", axis=1
            )
            
            fig_top_falhas = px.bar(top_falhas, x='Descrição Falha', y='Contagem',
                                   title='Top 10 Falhas Mais Frequentes',
                                   color='Contagem', height=500)
            fig_top_falhas.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_top_falhas, use_container_width=True)
            
            # Tabela com as top 10 falhas
            st.subheader('Detalhes das Top 10 Falhas')
            st.dataframe(top_falhas[['POINT_NAME', 'DESCRIPTION', 'DEVICE_TYPE', 'STATUS', 'Contagem']], use_container_width=True)
            
            # Botão para download dos dados processados
            csv = df_filtrado.drop(columns=['DATE_OBJ', 'DIA', 'MES', 'ANO']).to_csv(index=False, encoding='utf-8-sig', sep=';')
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

