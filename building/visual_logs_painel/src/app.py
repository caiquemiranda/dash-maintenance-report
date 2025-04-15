import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io

st.set_page_config(
    page_title="Analisador de TroubleLog",
    layout="wide"
)

st.title("Analisador de Log de Problemas")

# Função para processar o arquivo de log
def processar_troublelog(conteudo):
    # Expressão regular para extrair informações dos registros
    pattern = r'ENTRY (\d+)\s+(\d+:\d+:\d+)\s+(\w+) (\d+-\w+-\d+) (.+?)(?:\s{2,}|\n)(?:\s+(.+?)\s+(.+?))?(?:\n|$)'
    
    matches = re.findall(pattern, conteudo, re.MULTILINE)
    
    registros = []
    for match in matches:
        entry_num = match[0].strip()
        hora = match[1].strip()
        dia_semana = match[2].strip()
        data = match[3].strip()
        local = match[4].strip()
        
        tipo_dispositivo = match[5].strip() if len(match) > 5 and match[5] else ""
        status = match[6].strip() if len(match) > 6 and match[6] else ""
        
        # Converter data para formato padrão
        try:
            data_obj = datetime.strptime(f"{dia_semana} {data}", "%a %d-%b-%y")
            data_formatada = data_obj.strftime("%d-%m-%Y")
        except:
            data_formatada = data
        
        registros.append({
            "Entrada": entry_num,
            "Hora": hora,
            "Data": data_formatada,
            "Dia da Semana": dia_semana,
            "Local": local,
            "Tipo de Dispositivo": tipo_dispositivo,
            "Status": status
        })
    
    return pd.DataFrame(registros)

# Botão de upload do arquivo
uploaded_file = st.file_uploader("Carregue o arquivo TroubleLog.txt", type=["txt"])

if uploaded_file is not None:
    # Exibir informações sobre o arquivo
    st.success(f"Arquivo carregado: {uploaded_file.name}")
    
    # Ler o conteúdo do arquivo
    conteudo = uploaded_file.getvalue().decode("utf-8")
    
    # Processar o conteúdo do arquivo
    try:
        df = processar_troublelog(conteudo)
        
        # Exibir resumo dos dados
        st.subheader("Resumo dos Logs de Problemas")
        st.write(f"Total de registros encontrados: {len(df)}")
        
        # Filtragem
        st.subheader("Filtros")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Local' in df.columns and not df['Local'].empty:
                locais = ["Todos"] + sorted(df['Local'].unique().tolist())
                local_selecionado = st.selectbox("Filtrar por Local:", locais)
        
        with col2:
            if 'Status' in df.columns and not df['Status'].empty:
                status = ["Todos"] + sorted(df['Status'].unique().tolist())
                status_selecionado = st.selectbox("Filtrar por Status:", status)
        
        # Aplicar filtros
        filtered_df = df.copy()
        
        if local_selecionado != "Todos":
            filtered_df = filtered_df[filtered_df['Local'] == local_selecionado]
            
        if status_selecionado != "Todos":
            filtered_df = filtered_df[filtered_df['Status'] == status_selecionado]
        
        # Exibir tabela com os dados
        st.subheader("Tabela de Logs")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Opção para download dos dados processados
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download dos dados em CSV",
            data=csv,
            file_name="troublelog_processado.csv",
            mime="text/csv"
        )
        
        # Análise estatística básica
        st.subheader("Estatísticas")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Local' in df.columns and not df['Local'].empty:
                st.subheader("Ocorrências por Local")
                local_counts = df['Local'].value_counts().reset_index()
                local_counts.columns = ['Local', 'Contagem']
                st.dataframe(local_counts, use_container_width=True)
        
        with col2:
            if 'Status' in df.columns and not df['Status'].empty:
                st.subheader("Ocorrências por Status")
                status_counts = df['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Contagem']
                st.dataframe(status_counts, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
else:
    # Exibir instruções quando nenhum arquivo estiver carregado
    st.info("Por favor, carregue um arquivo TroubleLog.txt para análise.")
    
    # Exemplo de como os dados serão exibidos
    st.subheader("Formato de Saída")
    exemplo = pd.DataFrame({
        "Entrada": ["1", "2", "3"],
        "Hora": ["4:12:32", "4:17:08", "4:46:00"],
        "Data": ["15-01-2025", "15-01-2025", "15-01-2025"],
        "Dia da Semana": ["WED", "WED", "WED"],
        "Local": ["DF - FUNDO LOJA CHAME PIZZA L2 M3-57", "TROUBLES ACKNOWLEDGED AT MAIN PANEL", "BOMBA JOCKEY ACIONADA"],
        "Tipo de Dispositivo": ["SMOKE DETECTOR", "", "SUPERVISORY MONITOR"],
        "Status": ["EXCESSIVELY DIRTY", "", "ABNORMAL"]
    })
    st.dataframe(exemplo, use_container_width=True)
