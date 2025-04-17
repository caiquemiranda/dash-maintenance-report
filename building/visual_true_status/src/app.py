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
    # Ajuste: aceita M seguido de 1 ou mais dígitos
    regex_canal = re.compile(r"Channel (\d+) \((M\d+)\)")
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
    df['Atual_Simplex'] = pd.to_numeric(df['Atual_Simplex'], errors='coerce')
    df['Atual_Temp'] = pd.to_numeric(df['Atual_Temp'], errors='coerce')

    # Padronizar nome do canal para M01, M02, ...
    def padroniza_canal(canal):
        match = re.match(r'M(\d+)', canal)
        if match:
            return f"M{int(match.group(1)):02d}"
        return canal
    df['Canal'] = df['Canal'].apply(padroniza_canal)

    # Zerar valor de pico 255 e marcar dispositivos acionados
    df['Acionado_Max'] = False
    for col in ['Pico_Simplex', 'Pico_Temp']:
        if col in df.columns:
            mask = df[col] == 255
            df.loc[mask, col] = 0
            df.loc[mask, 'Acionado_Max'] = True

    # Slider para escolher o TOP
    st.sidebar.header('Configurações de Visualização')
    top_n = st.sidebar.slider('Escolha o TOP', min_value=5, max_value=50, value=20, step=1)

    st.header("Visualizações e Análises")
    # Layout horizontal organizado
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # Top N maiores valores de Pico (DF)
    with col1:
        st.subheader(f"Top {top_n} maiores valores de Pico (DF - Fumaça)")
        top_df = df[df['Tipo'] == 'DF'].sort_values('Pico_Simplex', ascending=False).head(top_n)
        st.dataframe(top_df[['Dispositivo', 'Descricao', 'Canal', 'Pico_Simplex', 'Status']])
        fig_df = px.bar(top_df, x='Pico_Simplex', y='Descricao', orientation='h', title=f'Top {top_n} Pico Simplex (DF)', labels={'Pico_Simplex':'Pico Simplex', 'Descricao':'Descrição'})
        st.plotly_chart(fig_df, use_container_width=True)

    # Top N maiores valores de Pico (DT)
    with col2:
        st.subheader(f"Top {top_n} maiores temperaturas (DT - Temperatura)")
        top_dt = df[df['Tipo'] == 'DT'].sort_values('Pico_Temp', ascending=False).head(top_n)
        st.dataframe(top_dt[['Dispositivo', 'Descricao', 'Canal', 'Pico_Temp', 'Status']])
        fig_dt = px.bar(top_dt, x='Pico_Temp', y='Descricao', orientation='h', title=f'Top {top_n} Pico Temperatura (DT)', labels={'Pico_Temp':'Pico Temperatura', 'Descricao':'Descrição'})
        st.plotly_chart(fig_dt, use_container_width=True)

    # Top N valores atuais (DF)
    with col3:
        st.subheader(f"Top {top_n} maiores valores atuais (DF - Fumaça)")
        top_df_atual = df[df['Tipo'] == 'DF'].sort_values('Atual_Simplex', ascending=False).head(top_n)
        st.dataframe(top_df_atual[['Dispositivo', 'Descricao', 'Canal', 'Atual_Simplex', 'Status']])
        fig_df_atual = px.bar(top_df_atual, x='Atual_Simplex', y='Descricao', orientation='h', title=f'Top {top_n} Valor Atual Simplex (DF)', labels={'Atual_Simplex':'Valor Atual', 'Descricao':'Descrição'})
        st.plotly_chart(fig_df_atual, use_container_width=True)

    # Top N valores atuais (DT)
    with col4:
        st.subheader(f"Top {top_n} maiores temperaturas atuais (DT - Temperatura)")
        top_dt_atual = df[df['Tipo'] == 'DT'].sort_values('Atual_Temp', ascending=False).head(top_n)
        st.dataframe(top_dt_atual[['Dispositivo', 'Descricao', 'Canal', 'Atual_Temp', 'Status']])
        fig_dt_atual = px.bar(top_dt_atual, x='Atual_Temp', y='Descricao', orientation='h', title=f'Top {top_n} Temperatura Atual (DT)', labels={'Atual_Temp':'Temperatura Atual', 'Descricao':'Descrição'})
        st.plotly_chart(fig_dt_atual, use_container_width=True)

    # Percentual de cada tipo
    st.subheader("Percentual de cada tipo de sensor no sistema")
    tipo_counts = df['Tipo'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo', 'Quantidade']
    fig_tipo = px.pie(tipo_counts, values='Quantidade', names='Tipo', title='Distribuição de Sensores DF x DT')
    st.plotly_chart(fig_tipo, use_container_width=True)

    # Quantidade de dispositivos por canal
    st.subheader("Quantidade de dispositivos por canal")
    canal_counts = df.groupby('Canal').size().reset_index(name='Quantidade')
    canal_counts = canal_counts.sort_values('Canal')
    fig_canal = px.bar(canal_counts, x='Canal', y='Quantidade', title='Dispositivos por Canal')
    st.plotly_chart(fig_canal, use_container_width=True)

    # Lista de dispositivos acionados no máximo (pico 255)
    st.subheader('Dispositivos acionados no máximo (Pico = 255)')
    acionados = df[df['Acionado_Max']]
    def highlight_red(s):
        return ['background-color: #ff4d4d' for _ in s]
    if not acionados.empty:
        st.dataframe(acionados[['Dispositivo', 'Descricao', 'Canal', 'Tipo', 'Status']].style.apply(highlight_red, axis=1))
    else:
        st.info('Nenhum dispositivo acionado no máximo.')
else:
    st.info("Faça upload do arquivo para visualizar os dados.") 