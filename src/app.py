#app.py

import streamlit as st
import re
import pandas as pd

def processar_arquivo(conteudo):
    # Dividir o conteúdo em linhas
    linhas = conteudo.split('\n')
    
    # Lista para armazenar os dados processados
    dados = []
    
    # Padrão regex para extrair informações (ajuste conforme seu arquivo)
    padrao = r'^(\w+)\s+(\d+)\s+(.+)$'
    
    for linha in linhas:
        if linha.strip():  # Ignorar linhas vazias
            match = re.match(padrao, linha)
            if match:
                nome, idade, descricao = match.groups()
                dados.append({
                    'Nome': nome,
                    'Idade': idade,
                    'Descrição': descricao
                })
    
    return pd.DataFrame(dados)

def main():
    st.title('Processador de Arquivos TXT')
    
    # Upload do arquivo
    arquivo = st.file_uploader("Faça upload do arquivo .txt", type=['txt'])
    
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

