import streamlit as st
import pandas as pd
from logs import extrair_informacoes, processar_valores_alarme, ler_arquivo_log

def main():
    st.title("Análise de Logs do Painel de Sensores de Incêndio")
    
    # Upload do arquivo
    uploaded_file = st.file_uploader("Escolha um arquivo de log (.txt)", type="txt")
    
    if uploaded_file is not None:
        # Ler o conteúdo do arquivo
        conteudo = uploaded_file.getvalue().decode("utf-8")
        
        try:
            # Processar os dados
            df = extrair_informacoes(conteudo)
            df = processar_valores_alarme(df)
            
            # Extrair localização do Label
            df['Location'] = df['Label'].apply(lambda x: x.split('-')[-2] if len(x.split('-')) > 2 else '')
            
            # Mostrar estatísticas básicas
            st.header("Visão Geral dos Dados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Distribuição por Canal")
                st.write(df['Channel'].value_counts())
            
            with col2:
                st.subheader("Estados dos Sensores")
                st.write(df['State'].value_counts())
            
            # Tabela com todos os dados
            st.header("Dados Detalhados")
            st.dataframe(df)
            
            # Sensores críticos
            st.header("Sensores com Valores Críticos")
            sensores_criticos = df[df['CurrentAlarmValue'] > 80].sort_values('CurrentAlarmValue', ascending=False)
            if not sensores_criticos.empty:
                st.dataframe(sensores_criticos[['DeviceNumber', 'Label', 'CurrentAlarmValue', 'CurrentAlarmPercent', 'Location']])
            else:
                st.info("Não foram encontrados sensores com valores críticos.")
            
            # Estatísticas dos valores de alarme
            st.header("Estatísticas dos Valores de Alarme")
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("Alarmes Atuais")
                st.write(df['CurrentAlarmValue'].describe())
            
            with col4:
                st.subheader("Picos de Alarme")
                st.write(df['PeakAlarmValue'].describe())
            
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
    
    else:
        st.info("Por favor, faça o upload de um arquivo de log para começar a análise.")

if __name__ == "__main__":
    main() 