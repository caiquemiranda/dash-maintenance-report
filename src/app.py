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
    
    # Extrair informações do cabeçalho
    header_info = {}
    for linha in linhas[:6]:
        if 'BRIDTFPP' in linha:
            match = re.search(r'Node\s+(\d+)\s+Rev\s+(\d+)\s+(\w+)\s+(\d{2}-\w{3}-\d{2})\s+(\d{2}:\d{2}:\d{2})', linha)
            if match:
                header_info['Node'] = match.group(1)
                header_info['Revision'] = match.group(2)
                header_info['Data_Log'] = match.group(4)
                header_info['Hora_Log'] = match.group(5)
    
    # Pular as linhas do cabeçalho
    linhas = linhas[6:]
    
    # Lista para armazenar os dados processados
    dados = []
    
    # Processar as linhas em grupos
    i = 0
    while i < len(linhas):
        if not linhas[i].strip():
            i += 1
            continue
            
        try:
            # Primeira linha: número e horário
            linha1_match = re.match(r'(\d+)\s+(\d{2}:\d{2}:\d{2})', linhas[i])
            if linha1_match:
                registro = {
                    'Sequência': linha1_match.group(1),
                    'Horário': linha1_match.group(2),
                    'Node': header_info.get('Node', 'N/A'),
                    'Revisão': header_info.get('Revision', 'N/A'),
                    'Data_Log': header_info.get('Data_Log', 'N/A'),
                }
                
                # Segunda linha: informações do dispositivo
                linha2 = linhas[i+1].strip()
                data_match = re.search(r'SUN\s+(\d{2}-\w{3}-\d{2})', linha2)
                if data_match:
                    registro['Data'] = data_match.group(1)
                
                device_match = re.search(r'(\d:\w+\-\d+\-\d+)\s+ESCRITORIO\s+ATENDIMENTO\s+RH\s+-\s+(\w+)', linha2)
                if device_match:
                    registro['Dispositivo'] = device_match.group(1)
                    registro['Localização'] = device_match.group(2)
                
                # Terceira linha: NODE e status
                linha3 = linhas[i+2].strip()
                node_match = re.search(r'\(NODE\s+(\d+)\)', linha3)
                if node_match:
                    registro['Node_Dispositivo'] = node_match.group(1)
                
                registro['Tipo'] = 'SMOKE DETECTOR' if 'SMOKE DETECTOR' in linha3 else 'OUTRO'
                registro['Status'] = 'BAD ANSWER' if 'BAD ANSWER' in linha3 else 'OK'
                
                dados.append(registro)
                i += 3
            else:
                i += 1
        except (AttributeError, IndexError):
            i += 1
    
    df = pd.DataFrame(dados)
    
    # Organizar as colunas em uma ordem lógica
    colunas = [
        'Sequência', 'Data', 'Horário', 'Dispositivo', 'Localização',
        'Tipo', 'Status', 'Node', 'Node_Dispositivo', 'Revisão', 'Data_Log'
    ]
    
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
                st.metric("Bad Answers", len(df[df['Status'] == 'BAD ANSWER']))
            with col3:
                st.metric("Registros OK", len(df[df['Status'] == 'OK']))
            
            # Botão para download dos dados processados
            csv = df.to_csv(index=False, encoding='utf-8-sig')
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

