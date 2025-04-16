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
    regex_dado = re.compile(r"^(\d{1,4}(?:-\d)?)\s+(.+?)\s+([*\d.]+/[\d ]+)\s+(\d{1,3}|--)\s+(\d{1,3}|--)\/(\s*\d{1,3}%|\s*--|\s*\d{1,3}C)\s+(\d{1,3}|--)\/(\s*\d{1,3}%|\s*--|\s*\d{1,3}C)\s+(\w{3})$")
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        canal_match = regex_canal.search(linha)
        if canal_match:
            canal_atual = canal_match.group(2)
            continue
        dado_match = regex_dado.match(linha)
        if dado_match and canal_atual:
            dados.append({
                'Canal': canal_atual,
                'Dispositivo': dado_match.group(1),
                'Descricao': dado_match.group(2),
                'Range/Valor': dado_match.group(3),
                'Media': dado_match.group(4),
                'Atual/Perc': dado_match.group(5) + '/' + dado_match.group(6),
                'Pico/Perc': dado_match.group(7) + '/' + dado_match.group(8),
                'Status': dado_match.group(9)
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