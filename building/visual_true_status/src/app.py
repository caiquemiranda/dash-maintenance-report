import streamlit as st
import pandas as pd
import re

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
    regex_df = re.compile(r"^(\d{1,4}(?:-\d)?)\s+(.+?)\s+([*\d.]+/[\d ]+)\s+(\d{1,3}|--)\s+(\d{1,3}|--)\/(\s*\d{1,3}%|\s*--|\s*\d{1,3}C)\s+(\d{1,3}|--)\/(\s*\d{1,3}%|\s*--|\s*\d{1,3}C)\s+(\w{3})$")
    # Regex para DT (temperatura)
    regex_dt = re.compile(r"^(\d{1,4}(?:-\d)?)\s+(.+?DT.*?)\s+(\d{1,3})C\/(\d{1,4})\s+--\s+(\d{1,3})\/(\d{1,3})C\s+(\d{1,3})\/(\d{1,3})C\s+(\w{3})$")
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        canal_match = regex_canal.search(linha)
        if canal_match:
            canal_atual = canal_match.group(2)
            continue
        # Tenta DT primeiro
        dado_dt = regex_dt.match(linha)
        if dado_dt and canal_atual:
            dados.append({
                'Canal': canal_atual,
                'Dispositivo': dado_dt.group(1),
                'Descricao': dado_dt.group(2),
                'Temp_Range': dado_dt.group(3),
                'Simplex_Range': dado_dt.group(4),
                'Media': None,
                'Atual_Simplex': dado_dt.group(5),
                'Atual_Temp': dado_dt.group(6),
                'Pico_Simplex': dado_dt.group(7),
                'Pico_Temp': dado_dt.group(8),
                'Status': dado_dt.group(9)
            })
            continue
        # Tenta DF (padrão)
        dado_df = regex_df.match(linha)
        if dado_df and canal_atual:
            # Extrai valores de range
            range_valor = dado_df.group(3).replace('*','').strip()
            if 'C' in range_valor:
                temp_range, simplex_range = range_valor.split('/')
                temp_range = temp_range.replace('C','').strip()
            else:
                temp_range = None
                simplex_range = range_valor.split('/')[1].strip()
            # Extrai valores atuais e picos
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
                'Status': dado_df.group(9)
            })
    return pd.DataFrame(dados)

# Upload do arquivo
dados = None
uploaded_file = st.file_uploader("Faça upload do arquivo TrueAlarmService.txt", type=["txt"])
if uploaded_file:
    dados = parse_true_alarm(uploaded_file)
    st.success(f"{len(dados)} linhas processadas.")
    st.dataframe(dados)
else:
    st.info("Faça upload do arquivo para visualizar os dados.") 