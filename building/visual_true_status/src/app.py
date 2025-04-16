import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(page_title="Dashboard TrueAlarm", layout="wide")
st.title("Dashboard TrueAlarm - Sensores")

# Função para parsear o arquivo

def parse_true_alarm(file):
    # Garante que o arquivo seja lido como texto
    if hasattr(file, 'read'):
        conteudo = file.read()
        if isinstance(conteudo, bytes):
            conteudo = conteudo.decode('utf-8', errors='ignore')
        linhas = conteudo.splitlines()
    else:
        linhas = file
    dados = []
    canal_atual = None
    regex_canal = re.compile(r"Channel (\d+) \((M\d)\)")
    # Regex para DF (padrão)
    regex_df = re.compile(r"^\s*(\d{1,4}(?:-\d)?)\s+(.+?)\s+([*\d.]+/[\d ]+)\s+(\d{1,3}|--)\s+(\d{1,3}|--)\/(\s*\d{1,3}%|\s*--|\s*\d{1,3}C)\s+(\d{1,3}|--)\/(\s*\d{1,3}%|\s*--|\s*\d{1,3}C)\s+(\w{3})$")
    # Regex para DT (temperatura) - identifica pelo valor inicial \d{1,3}C/\d{1,4}
    regex_dt = re.compile(r"^\s*(\d{1,4}(?:-\d)?)\s+(.+?)\s+(\d{1,3})C\/(\d{1,4})\s+(--|\d{1,3})\s+(\d{1,3})\/\s*(\d{1,3})C\s+(\d{1,3})\/\s*(\d{1,3})C\s+(\w{3})$")
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        canal_match = regex_canal.search(linha)
        if canal_match:
            canal_atual = canal_match.group(2)
            continue
        # Tenta DT primeiro (agora não depende da descrição)
        dado_dt = regex_dt.match(linha)
        if dado_dt and canal_atual:
            dados.append({
                'Canal': canal_atual,
                'Dispositivo': dado_dt.group(1),
                'Descricao': dado_dt.group(2),
                'Temp_Range': dado_dt.group(3),
                'Simplex_Range': dado_dt.group(4),
                'Media': dado_dt.group(5) if dado_dt.group(5) != '--' else None,
                'Atual_Simplex': dado_dt.group(6),
                'Atual_Temp': dado_dt.group(7),
                'Pico_Simplex': dado_dt.group(8),
                'Pico_Temp': dado_dt.group(9),
                'Status': dado_dt.group(10),
                'Tipo': 'DT'
            })
            continue
        # Tenta DF (padrão)
        dado_df = regex_df.match(linha)
        if dado_df and canal_atual:
            range_valor = dado_df.group(3).replace('*','').strip()
            if 'C' in range_valor:
                temp_range, simplex_range = range_valor.split('/')
                temp_range = temp_range.replace('C','').strip()
            else:
                temp_range = None
                simplex_range = range_valor.split('/')[1].strip()
            atual_simplex = dado_df.group(5).strip()
            atual_perc = dado_df.group(6).strip()
            pico_simplex = dado_df.group(7).strip()
            pico_perc = dado_df.group(8).strip()
            dados.append({
                'Canal': canal_atual,
                'Dispositivo': dado_df.group(1),
                'Descricao': dado_df.group(2),
                'Temp_Range': temp_range,
                'Simplex_Range': simplex_range,
                'Media': dado_df.group(4),
                'Atual_Simplex': atual_simplex,
                'Atual_Perc': atual_perc,
                'Pico_Simplex': pico_simplex,
                'Pico_Perc': pico_perc,
                'Status': dado_df.group(9),
                'Tipo': 'DF'
            })
    return pd.DataFrame(dados)

# Upload do arquivo
dados = None
uploaded_file = st.file_uploader("Faça upload do arquivo TrueAlarmService.txt", type=["txt"])
if uploaded_file:
    dados = parse_true_alarm(uploaded_file)
    st.success(f"{len(dados)} linhas processadas.")
    st.dataframe(dados)

    # Conversão de colunas para numérico onde possível
    df = dados.copy()
    df['Pico_Simplex'] = pd.to_numeric(df['Pico_Simplex'], errors='coerce')
    df['Pico_Temp'] = pd.to_numeric(df['Pico_Temp'], errors='coerce')

    st.header("Visualizações e Análises")
    col1, col2 = st.columns(2)

    # Maiores valores de DF
    with col1:
        st.subheader("Top 10 maiores valores de Pico (DF - Fumaça)")
        top_df = df[df['Tipo'] == 'DF'].sort_values('Pico_Simplex', ascending=False).head(10)
        st.dataframe(top_df[['Dispositivo', 'Descricao', 'Canal', 'Pico_Simplex', 'Status']])
        fig_df = px.bar(top_df, x='Pico_Simplex', y='Descricao', orientation='h', title='Top 10 Pico Simplex (DF)', labels={'Pico_Simplex':'Pico Simplex', 'Descricao':'Descrição'})
        st.plotly_chart(fig_df, use_container_width=True)

    # Maiores valores de DT
    with col2:
        st.subheader("Top 10 maiores temperaturas (DT - Temperatura)")
        top_dt = df[df['Tipo'] == 'DT'].sort_values('Pico_Temp', ascending=False).head(10)
        st.dataframe(top_dt[['Dispositivo', 'Descricao', 'Canal', 'Pico_Temp', 'Status']])
        fig_dt = px.bar(top_dt, x='Pico_Temp', y='Descricao', orientation='h', title='Top 10 Pico Temperatura (DT)', labels={'Pico_Temp':'Pico Temperatura', 'Descricao':'Descrição'})
        st.plotly_chart(fig_dt, use_container_width=True)

    # Percentual de cada tipo
    st.subheader("Percentual de cada tipo de sensor no sistema")
    tipo_counts = df['Tipo'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo', 'Quantidade']
    fig_tipo = px.pie(tipo_counts, values='Quantidade', names='Tipo', title='Distribuição de Sensores DF x DT')
    st.plotly_chart(fig_tipo, use_container_width=True)

    # Quantidade de dispositivos por canal
    st.subheader("Quantidade de dispositivos por canal")
    canal_counts = df.groupby('Canal').size().reset_index(name='Quantidade')
    fig_canal = px.bar(canal_counts, x='Canal', y='Quantidade', title='Dispositivos por Canal')
    st.plotly_chart(fig_canal, use_container_width=True)
else:
    st.info("Faça upload do arquivo para visualizar os dados.") 