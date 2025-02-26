#app.py

import streamlit as st
import re
import pandas as pd

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
        if not linhas[i].strip():  # Pular linhas vazias
            i += 1
            continue
            
        try:
            # Primeira linha contém número e horário
            linha1_match = re.match(r'(\d+)\s+(\d{2}:\d{2}:\d{2})', linhas[i])
            if linha1_match:
                numero = linha1_match.group(1)
                horario = linha1_match.group(2)
                
                # Segunda linha contém a data e localização
                linha2 = linhas[i+1].strip()
                data = re.search(r'SUN\s+(\d{2}-\w{3}-\d{2})', linha2).group(1)
                localizacao = re.search(r'ESCRITORIO\s+ATENDIMENTO\s+RH\s+-\s+(\w+)', linha2)
                localizacao = localizacao.group(1) if localizacao else "N/A"
                
                # Terceira linha contém o status
                linha3 = linhas[i+2].strip()
                status = "BAD ANSWER" if "BAD ANSWER" in linha3 else "OK"
                
                dados.append({
                    'Número': numero,
                    'Data': data,
                    'Horário': horario,
                    'Localização': localizacao,
                    'Status': status
                })
                
                i += 3  # Avançar para o próximo grupo de 3 linhas
            else:
                i += 1
        except (AttributeError, IndexError):
            i += 1
    
    return pd.DataFrame(dados)

def main():
    st.title('Processador de Logs TSW')
    
    # Upload do arquivo
    arquivo = st.file_uploader("Faça upload do arquivo de log .txt", type=['txt'])
    
    if arquivo is not None:
        # Ler o conteúdo do arquivo
        conteudo = arquivo.getvalue().decode('utf-8')
        
        try:
            # Processar o arquivo e criar DataFrame
            df = processar_arquivo(conteudo)
            
            # Exibir os dados originais
            st.subheader('Conteúdo Original')
            st.text(conteudo)
            
            # Exibir a tabela processada
            st.subheader('Dados Processados')
            st.dataframe(df)
            
            # Adicionar algumas métricas
            st.subheader('Métricas')
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Registros", len(df))
                st.metric("Bad Answers", len(df[df['Status'] == 'BAD ANSWER']))
            
            with col2:
                st.metric("Registros OK", len(df[df['Status'] == 'OK']))
            
            # Botão para download dos dados processados
            csv = df.to_csv(index=False)
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

