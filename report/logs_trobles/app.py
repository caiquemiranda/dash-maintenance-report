import re

def formatar_arquivo(arquivo_entrada, arquivo_saida, linhas_a_ignorar=5):
    """
    Formata um arquivo TXT, consolidando todos os dados de cada registro em uma única linha,
    utilizando expressões regulares para identificar o início de novos registros. Ignora as primeiras
    linhas_a_ignorar linhas do arquivo.

    Args:
        arquivo_entrada (str): Caminho para o arquivo de entrada.
        arquivo_saida (str): Caminho para o arquivo de saída.
        linhas_a_ignorar (int, optional): Número de linhas a serem ignoradas no início do arquivo.
            Padrão: 5.
    """

    with open(arquivo_entrada, 'r', encoding='latin-1') as entrada, open(arquivo_saida, 'w') as saida:
        linha_atual = ""
        padrao = r"^\s*(\d+)\s+(\d{2}:\d{2}:\d{2})"  # Expressão regular para identificar o início de uma nova linha

        # Ignora as primeiras 'linhas_a_ignorar' linhas
        for _ in range(linhas_a_ignorar):
            next(entrada)

        for linha in entrada:
            linha = linha.strip()

            if re.match(padrao, linha):
                # Escreve a linha completa no arquivo de saída
                if linha_atual:
                    saida.write(linha_atual.strip() + "\n")
                linha_atual = linha
            else:
                # Continua a linha atual
                linha_atual += " " + linha

        # Escreve a última linha, caso haja
        if linha_atual:
            saida.write(linha_atual.strip() + "\n")

# Exemplo de uso
arquivo_entrada = "dados.txt"
arquivo_saida = "arquivo_formatado.txt"
formatar_arquivo(arquivo_entrada, arquivo_saida, linhas_a_ignorar=5)  # Ignora as primeiras 5 linhas

import csv

def processar_dados_para_csv(arquivo_entrada, arquivo_saida):
    """
    Processa um arquivo de texto contendo os dados e gera um arquivo CSV.

    Args:
        arquivo_entrada: Caminho para o arquivo de texto.
        arquivo_saida: Caminho para o arquivo CSV de saída.
    """

    padrao = (
    r"(\d+)\s+"                     # ID (um ou mais dígitos seguidos de espaço)
    r"(\d{2}:\d{2}:\d{2})\s+"       # TIME (hh:mm:ss seguido de espaço)
    r"([\w:.\-M]+)\s+"              # TAG (permitindo letras, números, :, ., -, M)
    r"(.+?)\s+"                     # DESCRIPTION (captura tudo até a DATA)
    r"([A-Z]{3} \d{2}-[A-Z]{3}-\d{2})\s+"  # DATE (ex: MON 30-DEC-24)
    r"\(NODE (\d+)\)\s+"            # NODE (captura apenas o número do nó)
    r"([\w\s]+?)\s{2,}"             # TYPE (captura palavras e espaços até os múltiplos espaços)
    r"(.+)"                         # STATUS (captura qualquer coisa restante)
    )

    with open(arquivo_entrada, 'r') as entrada, open(arquivo_saida, 'w', newline='') as saida:
        writer = csv.writer(saida)
        # Escreve o cabeçalho do CSV
        writer.writerow(['ID', 'TIME', 'TAG', 'DESCRIPTION', 'DATA', 'NODE', 'TYPE', 'STATUS'])

        for linha in entrada:
            linha = linha.strip()
            match = re.match(padrao, linha)
            if match:
                grupos = match.groups()
                writer.writerow(grupos)

# Exemplo de uso
arquivo_entrada = 'arquivo_formatado.txt'
arquivo_saida = 'dados_processados.csv'
processar_dados_para_csv(arquivo_entrada, arquivo_saida)

import pandas as pd

dados = pd.read_csv('dados_processados.csv')
dados.head(100)
