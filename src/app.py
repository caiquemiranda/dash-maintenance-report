#app.py

import streamlit as st
import re
import pandas as pd
import datetime

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
    
    # Processar as linhas em grupos de 4
    i = 0
    while i < len(linhas):
        if not linhas[i].strip():
            i += 1
            continue
            
        try:
            # Primeira linha: ID e TIME
            linha1_match = re.match(r'(\d+)\s+(\d{2}:\d{2}:\d{2})', linhas[i])
            if linha1_match:
                registro = {
                    'ID': linha1_match.group(1),
                    'TIME': linha1_match.group(2)
                }
                
                # Obter o resto da primeira linha (início da DESCRIPTION)
                point_descr = re.search(r'\d{2}:\d{2}:\d{2}\s+(.*)', linhas[i])
                if point_descr:
                    point_desc_texto = point_descr.group(1).strip()
                    
                    # Extrair o POINT_NAME e o início da DESCRIPTION
                    point_match = re.match(r'([\d:]\S+)\s+(.*)', point_desc_texto)
                    if point_match:
                        registro['POINT_NAME'] = point_match.group(1)
                        description = point_match.group(2)
                
                # Segunda linha: continuação da DESCRIPTION
                if i + 1 < len(linhas) and linhas[i+1].strip():
                    desc_continuation = linhas[i+1].strip()
                    if description:
                        # Juntar as duas partes da descrição
                        description = description + " " + desc_continuation
                    else:
                        description = desc_continuation
                    
                registro['DESCRIPTION'] = description
                
                # Terceira linha: DATA e NODE
                if i + 2 < len(linhas) and linhas[i+2].strip():
                    linha3 = linhas[i+2].strip()
                    
                    # Extrair DATA
                    data_match = re.search(r'SUN\s+(\d{2})-(\w{3})-(\d{2})', linha3)
                    if data_match:
                        dia = data_match.group(1)
                        mes_abrev = data_match.group(2)
                        ano = data_match.group(3)
                        
                        # Converter o mês de abreviação para número
                        meses = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
                                'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
                        mes = meses.get(mes_abrev, '01')
                        
                        # Formatar a data como DD/MM/YYYY
                        registro['DATE'] = f"{dia}/{mes}/20{ano}"
                    
                    # Extrair NODE
                    node_match = re.search(r'\(NODE\s+(\d+)\)', linha3)
                    if node_match:
                        registro['NODE'] = node_match.group(1)
                
                # Quarta linha: DEVICE_TYPE e STATUS
                if i + 3 < len(linhas) and linhas[i+3].strip():
                    linha4 = linhas[i+3].strip()
                    
                    # Extrair DEVICE_TYPE
                    if 'SMOKE DETECTOR' in linha4:
                        registro['DEVICE_TYPE'] = 'SMOKE DETECTOR'
                    elif 'Quick Alert Signal' in linha4:
                        registro['DEVICE_TYPE'] = 'Quick Alert Signal'
                    elif 'AUXILIARY RELAY' in linha4:
                        registro['DEVICE_TYPE'] = 'AUXILIARY RELAY'
                    else:
                        device_match = re.match(r'([^A-Z]+)(?:\s+[A-Z]+\s+[A-Z]+)?', linha4)
                        if device_match:
                            registro['DEVICE_TYPE'] = device_match.group(1).strip()
                        else:
                            registro['DEVICE_TYPE'] = 'N/A'
                    
                    # Extrair STATUS
                    if 'BAD ANSWER' in linha4:
                        registro['STATUS'] = 'BAD ANSWER'
                    elif 'SHORT CIRCUIT TROUBLE' in linha4:
                        registro['STATUS'] = 'SHORT CIRCUIT TROUBLE'
                    else:
                        status_match = re.search(r'[A-Z]+\s+[A-Z]+$', linha4)
                        if status_match:
                            registro['STATUS'] = status_match.group(0)
                        else:
                            registro['STATUS'] = 'N/A'
                
                dados.append(registro)
                i += 4  # Avançar para o próximo grupo de 4 linhas
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
    
    return df[colunas]

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
            
            # Exibir os dados originais
            with st.expander("Ver conteúdo original"):
                st.text(conteudo)
            
            # Exibir a tabela processada
            st.subheader('Dados Processados')
            st.dataframe(df, use_container_width=True)
            
            # Adicionar algumas métricas
            st.subheader('Métricas')
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Registros", len(df))
            with col2:
                st.metric("Bad Answers", len(df[df['STATUS'] == 'BAD ANSWER']))
            with col3:
                st.metric("Short Circuit Troubles", len(df[df['STATUS'] == 'SHORT CIRCUIT TROUBLE']))
            
            # Gráfico de contagem por tipo de dispositivo
            st.subheader('Contagem por Tipo de Dispositivo')
            device_count = df['DEVICE_TYPE'].value_counts().reset_index()
            device_count.columns = ['Tipo de Dispositivo', 'Contagem']
            st.bar_chart(device_count.set_index('Tipo de Dispositivo'))
            
            # Botão para download dos dados processados
            csv = df.to_csv(index=False, encoding='utf-8-sig', sep=';')
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

