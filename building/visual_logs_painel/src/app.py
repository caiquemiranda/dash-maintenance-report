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
    # Remover cabeçalhos de página
    conteudo = re.sub(r'-{80,}\nService Port\s+Page \d+\nReport 2 : Trouble Historical Log\s+\d+:\d+:\d+\s+\w+ \d+-\w+-\d+\n-{80,}', '', conteudo)
    
    # Dividir o conteúdo em linhas e remover linhas vazias
    linhas = [linha for linha in conteudo.split('\n') if linha.strip()]
    
    registros = []
    i = 0
    total_linhas = len(linhas)
    
    while i < total_linhas:
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
        
        i += 1
    
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
        
        # Exibir resumo dos dados
        st.subheader("Resumo dos Logs de Problemas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de registros", len(df))
        with col2:
            if 'Local' in df.columns:
                st.metric("Locais únicos", df['Local'].nunique())
        with col3:
            if 'Status' in df.columns:
                st.metric("Status diferentes", df['Status'].nunique())
        
        # Filtragem
        st.subheader("Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Local' in df.columns and not df['Local'].empty:
                locais = ["Todos"] + sorted(df['Local'].unique().tolist())
                local_selecionado = st.selectbox("Filtrar por Local:", locais)
        
        with col2:
            if 'Status' in df.columns and not df['Status'].empty:
                status = ["Todos"] + sorted(df['Status'].unique().tolist())
                status_selecionado = st.selectbox("Filtrar por Status:", status)
                
        with col3:
            if 'Tipo de Dispositivo' in df.columns and not df['Tipo de Dispositivo'].empty:
                dispositivos = ["Todos"] + sorted(df['Tipo de Dispositivo'].unique().tolist())
                dispositivo_selecionado = st.selectbox("Filtrar por Dispositivo:", dispositivos)
        
        # Aplicar filtros
        filtered_df = df.copy()
        
        if local_selecionado != "Todos":
            filtered_df = filtered_df[filtered_df['Local'] == local_selecionado]
            
        if status_selecionado != "Todos":
            filtered_df = filtered_df[filtered_df['Status'] == status_selecionado]
            
        if dispositivo_selecionado != "Todos":
            filtered_df = filtered_df[filtered_df['Tipo de Dispositivo'] == dispositivo_selecionado]
        
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
        tab1, tab2, tab3 = st.tabs(["Locais", "Status", "Dispositivos"])
        
        with tab1:
            if 'Local' in df.columns and not df['Local'].empty:
                st.subheader("Ocorrências por Local")
                local_counts = df['Local'].value_counts().reset_index()
                local_counts.columns = ['Local', 'Contagem']
                st.dataframe(local_counts, use_container_width=True)
        
        with tab2:
            if 'Status' in df.columns and not df['Status'].empty:
                st.subheader("Ocorrências por Status")
                status_counts = df['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Contagem']
                st.dataframe(status_counts, use_container_width=True)
                
        with tab3:
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
