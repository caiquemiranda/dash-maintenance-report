import pandas as pd
import re
import datetime

def tentar_decodificar(arquivo):
    """Tenta decodificar o arquivo com diferentes codificações"""
    codificacoes = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for codec in codificacoes:
        try:
            return arquivo.getvalue().decode(codec)
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError("Não foi possível decodificar o arquivo com nenhuma das codificações conhecidas")

def converter_data(dia_semana, dia, mes_abrev, ano):
    """Converte data do formato texto para formato DD/MM/YYYY"""

    meses = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
            'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
    mes = meses.get(mes_abrev, '01')
    
    return f"{dia}/{mes}/20{ano}" 
