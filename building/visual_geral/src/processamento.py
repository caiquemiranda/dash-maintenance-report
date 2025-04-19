import pandas as pd
import re

def processar_arquivo_pontos(arquivo, formato='csv'):
    """
    Processa o arquivo de lista de pontos para um formato padronizado
    
    Parâmetros:
    arquivo (file): Arquivo enviado por upload (BytesIO)
    formato (str): Formato do arquivo (csv, txt)
    
    Retorna:
    DataFrame pandas com as colunas padronizadas
    """
    # Lista de codificações para tentar
    codificacoes = ['latin1', 'cp1252', 'utf-8-sig', 'utf-8']
    
    # Tentar diferentes codificações
    for codificacao in codificacoes:
        try:
            if formato == 'csv':
                # Detectar o separador automaticamente
                df = pd.read_csv(arquivo, sep=';', engine='python', encoding=codificacao)
            else:
                # Tratar como txt
                df = pd.read_csv(arquivo, sep=';', engine='python', encoding=codificacao)
                
            # Se chegou aqui, a leitura foi bem-sucedida
            break
        except UnicodeDecodeError:
            # Tentar próxima codificação
            if codificacao == codificacoes[-1]:
                # Se for a última codificação, não há mais o que tentar
                raise Exception("Não foi possível decodificar o arquivo. Verifique a codificação.")
            # Resetar o ponteiro do arquivo para o início
            arquivo.seek(0)
            continue
    
    # Renomear colunas para o padrão esperado
    if 'Column1' in df.columns and 'Column2' in df.columns and 'Column3' in df.columns and 'Column4' in df.columns:
        df = df.rename(columns={
            'Column1': 'id_disp',
            'Column2': 'type',
            'Column3': 'action',
            'Column4': 'description'
        })
    
    # Limpar espaços em branco dos dados
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    
    # Se faltar alguma coluna essencial, adicionar vazia
    colunas_essenciais = ['id_disp', 'type', 'action', 'description']
    for col in colunas_essenciais:
        if col not in df.columns:
            df[col] = ''
    
    return df[colunas_essenciais]

def extrair_dados_dispositivo(id_disp):
    """
    Extrai informações adicionais do código do dispositivo usando regex
    
    Exemplo: M1-249-0 -> {modulo: 'M1', numero: 249, sub: 0}
    
    Parâmetros:
    id_disp (str): ID do dispositivo
    
    Retorna:
    dict com as informações extraídas
    """
    # Padrão para dispositivos do tipo M1-249-0
    padrao = r'^([A-Za-z]+)(\d+)-(\d+)-(\d+)$'
    match = re.match(padrao, id_disp.strip())
    
    if match:
        return {
            'prefixo': match.group(1),
            'modulo': int(match.group(2)),
            'numero': int(match.group(3)),
            'sub': int(match.group(4))
        }
    
    return {
        'prefixo': '',
        'modulo': 0,
        'numero': 0,
        'sub': 0
    }

def enriquecer_dados(df):
    """
    Adiciona colunas extras com informações extraídas dos ids dos dispositivos
    
    Parâmetros:
    df (DataFrame): DataFrame com os dados processados
    
    Retorna:
    DataFrame enriquecido com novas colunas
    """
    # Copiar para não modificar o original
    df_enriquecido = df.copy()
    
    # Aplicar função de extração em cada ID de dispositivo
    info_dispositivos = df_enriquecido['id_disp'].apply(extrair_dados_dispositivo)
    
    # Expandir o dicionário em novas colunas
    info_df = pd.json_normalize(info_dispositivos)
    
    # Concatenar com os dados originais
    df_resultado = pd.concat([df_enriquecido, info_df], axis=1)
    
    return df_resultado 