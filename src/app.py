#app.py

import streamlit as st
import re
import pandas as pd

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
    
    # Processar as linhas em grupos de 3
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
                
                # Segunda linha: POINT_NAME e DESCRIPTION
                if i + 1 < len(linhas):
                    linha2 = linhas[i+1].strip()
                    point_match = re.match(r'([\d:]\S+)\s+(.*)', linha2)
                    if point_match:
                        registro['POINT_NAME'] = point_match.group(1)
                        registro['DESCRIPTION'] = point_match.group(2)
                        
                    # Extrair DATA
                    data_match = re.search(r'SUN\s+(\d{2}-\w{3}-\d{2})', linha2)
                    if data_match:
                        registro['DATE'] = data_match.group(0)  # Incluir "SUN" na data
                
                # Terceira linha: NODE, DEVICE_TYPE e STATUS
                if i + 2 < len(linhas):
                    linha3 = linhas[i+2].strip()
                    
                    # Extrair NODE
                    node_match = re.search(r'(\(NODE\s+\d+\))', linha3)
                    if node_match:
                        registro['NODE'] = node_match.group(1)
                    
                    # Extrair DEVICE_TYPE e STATUS
                    if 'SMOKE DETECTOR' in linha3:
                        registro['DEVICE_TYPE'] = 'SMOKE DETECTOR'
                        registro['STATUS'] = 'BAD ANSWER' if 'BAD ANSWER' in linha3 else 'OK'
                    elif 'Quick Alert Signal' in linha3:
                        registro['DEVICE_TYPE'] = 'Quick Alert Signal'
                        registro['STATUS'] = 'SHORT CIRCUIT TROUBLE' if 'SHORT CIRCUIT TROUBLE' in linha3 else 'OK'
                    else:
                        registro['DEVICE_TYPE'] = 'OUTRO'
                        registro['STATUS'] = linha3.split()[-1] if linha3 else 'N/A'
                
                dados.append(registro)
                i += 3
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

