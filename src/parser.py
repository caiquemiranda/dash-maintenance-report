import pandas as pd
import re
import sys
import os

# Adicionar o diretório pai ao path para encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar com importação absoluta
import src.utils as utils

def processar_arquivo(conteudo):
    """Processa o arquivo de log e retorna um DataFrame"""
    # Dividir o conteúdo em linhas
    linhas = conteudo.split('\n')
    
    # Pular as primeiras 6 linhas de cabeçalho
    linhas = linhas[6:]
    
    # Lista para armazenar os dados processados
    dados = []
    
    # Processar as linhas
    i = 0
    while i < len(linhas):
        # Pular linhas vazias
        if not linhas[i].strip():
            i += 1
            continue
            
        try:
            # Verificar se a linha começa com um ID e horário
            linha1_match = re.match(r'^\s*(\d+)\s+(\d{2}:\d{2}:\d{2})', linhas[i])
            if linha1_match:
                id_registro = linha1_match.group(1)
                horario = linha1_match.group(2)
                
                # Inicializar o registro com valores padrão
                registro = {
                    'ID': id_registro,
                    'TIME': horario,
                    'POINT_NAME': 'N/A',
                    'DESCRIPTION': 'N/A',
                    'DATE': 'N/A',
                    'NODE': 'N/A',
                    'DEVICE_TYPE': 'N/A',
                    'STATUS': 'N/A'
                }
                
                # Extrair POINT_NAME e DESCRIPTION
                linha_resto = linhas[i][len(id_registro):].strip()
                linha_resto = linha_resto[8:].strip()  # Remover o horário (8 caracteres: HH:MM:SS)
                
                if linha_resto:
                    # Tentar extrair o POINT_NAME
                    point_match = re.match(r'([\d:][^\ ]+)', linha_resto)
                    if point_match:
                        registro['POINT_NAME'] = point_match.group(1)
                        description = linha_resto[len(point_match.group(1)):].strip()
                        registro['DESCRIPTION'] = description
                    else:
                        # Se não conseguir extrair um POINT_NAME, considerar tudo como DESCRIPTION
                        registro['DESCRIPTION'] = linha_resto
                
                # Verificar se existem mais linhas para este registro
                linhas_registro = [linhas[i]]
                j = i + 1
                linha_data_encontrada = False
                linha_device_encontrada = False
                
                # Coletar todas as linhas do registro atual até encontrar o próximo registro ou fim do arquivo
                while j < len(linhas):
                    linha_atual = linhas[j].strip()
                    
                    # Se a linha começar com um número, é o início do próximo registro
                    if re.match(r'^\s*\d+\s+\d{2}:\d{2}:\d{2}', linhas[j]):
                        break
                    
                    if linha_atual:
                        linhas_registro.append(linhas[j])
                        
                        # Verificar se é uma linha com DATA e NODE
                        data_match = re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN)\s+(\d{2})-(\w{3})-(\d{2})', linha_atual)
                        node_match = re.search(r'\(NODE\s+(\d+)\)', linha_atual)
                        
                        if data_match and not linha_data_encontrada:
                            linha_data_encontrada = True
                            dia_semana = data_match.group(1)
                            dia = data_match.group(2)
                            mes_abrev = data_match.group(3)
                            ano = data_match.group(4)
                            
                            # Converter para formato DD/MM/YYYY
                            registro['DATE'] = utils.converter_data(dia_semana, dia, mes_abrev, ano)
                        
                        if node_match:
                            registro['NODE'] = node_match.group(1)
                        
                        # Verificar se é uma linha com DEVICE_TYPE e STATUS
                        if not linha_device_encontrada and not data_match:
                            # Se a linha não contém data e não está vazia, pode ser a linha de device/status
                            device_types = [
                                'SMOKE DETECTOR', 'Quick Alert Signal', 'AUXILIARY RELAY', 'PULL STATION',
                                'SUPERVISORY MONITOR', 'SIGNAL CIRCUIT', 'MAPNET ISOLATOR', 'FIRE MONITOR ZONE',
                                'TROUBLE RELAY'
                            ]
                            
                            for device in device_types:
                                if device in linha_atual:
                                    linha_device_encontrada = True
                                    registro['DEVICE_TYPE'] = device
                                    
                                    # Extrair STATUS - tudo que vem depois do DEVICE_TYPE
                                    status_part = linha_atual[linha_atual.find(device) + len(device):].strip()
                                    if status_part:
                                        registro['STATUS'] = status_part
                                    break
                            
                            # Caso especial para linhas que não contêm um DEVICE_TYPE conhecido
                            if not linha_device_encontrada and 'TROUBLE GLOBAL' in linha_atual:
                                registro['DEVICE_TYPE'] = 'TROUBLE GLOBAL'
                                if 'ACKNOWLEDGE' in linha_atual:
                                    registro['STATUS'] = 'ACKNOWLEDGE'
                    
                    j += 1
                
                # Atualizar a descrição com linhas adicionais se necessário
                if len(linhas_registro) > 1 and 'DESCRIPTION' in registro:
                    # Verificar se há linhas de continuação da descrição
                    descricao_completa = registro['DESCRIPTION']
                    
                    # Para o caso específico de TROUBLE RELAY, concatenar a segunda linha à descrição
                    segunda_linha = linhas_registro[1].strip() if len(linhas_registro) > 1 else ""
                    if segunda_linha and not re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN)', segunda_linha) and not any(device in segunda_linha for device in device_types):
                        if descricao_completa != 'N/A':
                            descricao_completa += " " + segunda_linha
                        else:
                            descricao_completa = segunda_linha
                    
                    registro['DESCRIPTION'] = descricao_completa
                
                dados.append(registro)
                i = j  # Avançar para o próximo registro
            else:
                i += 1
        except Exception as e:
            print(f"Erro ao processar linha {i}: {str(e)}")
            i += 1
    
    # Criar DataFrame com as colunas na ordem especificada
    colunas = ['ID', 'TIME', 'POINT_NAME', 'DESCRIPTION', 'DATE', 'NODE', 'DEVICE_TYPE', 'STATUS']
    df = pd.DataFrame(dados)
    
    # Garantir que todas as colunas existam
    for coluna in colunas:
        if coluna not in df.columns:
            df[coluna] = 'N/A'
    
    # Converter a coluna de data para datetime
    df['DATE_OBJ'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y', errors='coerce')
    
    return df[colunas + ['DATE_OBJ']] 