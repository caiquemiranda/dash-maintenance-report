import pandas as pd
import re
import datetime

def ler_arquivo_log(caminho):
    """Lê o arquivo de log e retorna seu conteúdo"""
    with open(caminho, 'r', encoding='utf-8') as file:
        return file.read()
    
def extrair_informacoes(conteudo):
    """Extrai informações do conteúdo do log usando regex"""
    # Padrão para encontrar as linhas de dados
    padrao = r'^\s*(\d+)\s+([\w\-\d]+)\s+([*]?[\d\.]+/\d+)\s+(\d+)\s+(\d+/\s*\d+%)\s+(\d+/\s*\d+%)\s+(\w+)'
    
    dados = []
    channel = None
    data_hora = None
    
    for linha in conteudo.split('\n'):
        # Extrair informação do canal
        canal_match = re.search(r'Channel (\d+) \((M\d+)\)', linha)
        if canal_match:
            channel = canal_match.group(1)
            continue
            
        # Extrair data e hora
        data_match = re.search(r'(\d{2}:\d{2}:\d{2})\s+(\w{3})\s+(\d{2})-(\w{3})-(\d{2})', linha)
        if data_match:
            hora = data_match.group(1)
            dia_semana = data_match.group(2)
            dia = data_match.group(3)
            mes = data_match.group(4)
            ano = data_match.group(5)
            data_hora = f"{dia}/{mes}/20{ano} {hora}"
            continue
            
        # Extrair dados dos sensores
        match = re.match(padrao, linha)
        if match:
            dev_num, label, alarm_at, avg_val, current_alarm, peak_alarm, state = match.groups()
            
            dados.append({
                'Channel': channel,
                'DateTime': data_hora,
                'DeviceNumber': dev_num.strip(),
                'Label': label.strip(),
                'AlarmAt': alarm_at.strip(),
                'AverageValue': avg_val.strip(),
                'CurrentAlarm': current_alarm.strip(),
                'PeakAlarm': peak_alarm.strip(),
                'State': state.strip()
            })
    
    return pd.DataFrame(dados)

def processar_valores_alarme(df):
    """Processa as colunas de alarme separando valores e percentuais"""
    
    # Função auxiliar para extrair valor numérico do percentual
    def extrair_percentual(valor):
        return int(re.search(r'(\d+)%', valor).group(1))
    
    def extrair_valor(valor):
        return int(valor.split('/')[0].strip())
    
    # Processar AlarmAt - remover o prefixo e manter apenas o valor após a /
    df['AlarmAt'] = df['AlarmAt'].apply(lambda x: x.split('/')[-1])
    
    # Processar CurrentAlarm
    df['CurrentAlarmValue'] = df['CurrentAlarm'].apply(extrair_valor)
    df['CurrentAlarmPercent'] = df['CurrentAlarm'].apply(extrair_percentual)
    
    # Processar PeakAlarm
    df['PeakAlarmValue'] = df['PeakAlarm'].apply(extrair_valor)
    df['PeakAlarmPercent'] = df['PeakAlarm'].apply(extrair_percentual)
    
    # Remover as colunas originais
    df = df.drop(['CurrentAlarm', 'PeakAlarm'], axis=1)
    
    return df

# Ler e processar o arquivo
caminho_arquivo = 'data/TrueAlarmService.txt'
conteudo = ler_arquivo_log(caminho_arquivo)
df = extrair_informacoes(conteudo)
df = processar_valores_alarme(df)

print(df.head())