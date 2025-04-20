import streamlit as st
import pandas as pd
import os
import sys
import sqlite3
import json
from datetime import datetime, date
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import dash
from dash import html, dcc, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
from flask import Flask, request
import db
from dash.exceptions import PreventUpdate
import calendar
import base64
import io

# Importar módulos criados
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db
from db import obter_dispositivos, obter_dados_dispositivos, buscar_testes_dispositivos, salvar_teste_dispositivos, obter_lista_clientes, buscar_manutencao_mensal, buscar_manutencao_anual, salvar_acao_corretiva, buscar_acoes_corretivas
import processamento

# Inicializar o banco de dados
db.init_db()

# Simulação de clientes cadastrados (depois virá do banco)
CLIENTES = ['BRD', 'BYR', 'AERO', 'BSC']

# Simulação de navegação
MENU_OPCOES = [
    'Histórico Geral',
    'Saúde do Sistema',
    'Lista Dispositivos',
    'Plano de Manutenção',
    'Manutenção Mensal',
    'TrueService',
    'TrueAlarm',
    'Upload de Dados'
]

def main():
    st.set_page_config(page_title="Dashboard de Manutenção", layout="wide")

    # Sidebar: seleção de cliente
    st.sidebar.header("Selecione o Cliente")
    cliente = st.sidebar.selectbox("Cliente", CLIENTES)

    # Exibir título principal apenas se cliente selecionado
    if cliente:
        st.title(f"Dashboard de Manutenção - {cliente}")
    else:
        st.title("Dashboard de Manutenção")

    # Sidebar: menu de navegação (aparece só após seleção do cliente)
    if cliente:
        st.sidebar.header("Menu")
        # CSS global para estilizar o botão selecionado
        st.markdown('''
            <style>
            div[data-testid="stSidebar"] button.selected-btn {
                background-color: #ff4b4b !important;
                color: white !important;
                border: none !important;
            }
            </style>
        ''', unsafe_allow_html=True)
        if 'opcao_menu' not in st.session_state:
            st.session_state['opcao_menu'] = MENU_OPCOES[0]
        for op in MENU_OPCOES:
            btn_class = "selected-btn" if op == st.session_state['opcao_menu'] else ""
            if st.sidebar.button(op, key=op, use_container_width=True, help=None):
                st.session_state['opcao_menu'] = op
            # Aplica a classe CSS ao botão selecionado
            if btn_class:
                st.markdown(f'''<style>div[data-testid="stSidebar"] button[data-testid="baseButton"][aria-label="{op}"] {{background-color: #ff4b4b !important; color: white !important; border: none !important;}}</style>''', unsafe_allow_html=True)
        opcao = st.session_state['opcao_menu']
    else:
        opcao = None

    # Conteúdo principal
    if not cliente:
        st.info("Selecione um cliente para começar.")
        return

    if opcao == 'Upload de Dados':
        pagina_upload(cliente)
    elif opcao == 'Lista Dispositivos':
        pagina_dispositivos(cliente)
    elif opcao == 'Plano de Manutenção':
        pagina_plano_manutencao(cliente)
    elif opcao == 'Manutenção Mensal':
        pagina_manutencao_mensal(cliente)
    elif opcao == 'Saúde do Sistema':
        pagina_saude_sistema(cliente)
    else:
        st.write(f"Página: {opcao} (em construção)")

def extrair_laco(id_disp):
    """Extrai as duas primeiras letras do id_disp que representam o laço"""
    if isinstance(id_disp, str) and len(id_disp) >= 2:
        return id_disp.strip()[:2]
    return ""

def pagina_dispositivos(cliente):
    st.subheader(f"Lista de Dispositivos - {cliente}")
    
    # Buscar dados do banco de dados
    dados = db.buscar_pontos(cliente)
    
    if not dados:
        st.info(f"Nenhum dispositivo cadastrado para {cliente}. Use a página de Upload para adicionar.")
        return
    
    # Mostrar dados em DataFrame
    df = pd.DataFrame(dados)
    
    # Extrair informação de laço a partir das duas primeiras letras do id_disp
    df['laco'] = df['id_disp'].apply(extrair_laco)
    
    # Adicionar opções de filtro
    st.markdown("### Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    # Filtro por tipo
    with col1:
        tipos_unicos = sorted(df['type'].unique())
        tipo_selecionado = st.multiselect("Filtrar por Tipo:", tipos_unicos)
    
    # Filtro por laço
    with col2:
        lacos_unicos = sorted(df['laco'].unique())
        laco_selecionado = st.multiselect("Filtrar por Laço:", lacos_unicos)
    
    # Filtro por texto na descrição
    with col3:
        texto_busca = st.text_input("Buscar na descrição:")
    
    # Opção para mostrar/ocultar UNUSED
    with col4:
        mostrar_unused = st.checkbox("Mostrar UNUSED", value=True)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    # Filtro por tipo
    if tipo_selecionado:
        df_filtrado = df_filtrado[df_filtrado['type'].isin(tipo_selecionado)]
    
    # Filtro por laço
    if laco_selecionado:
        df_filtrado = df_filtrado[df_filtrado['laco'].isin(laco_selecionado)]
    
    # Filtro por texto na descrição
    if texto_busca:
        df_filtrado = df_filtrado[df_filtrado['description'].str.contains(texto_busca, case=False, na=False)]
    
    # Filtro UNUSED
    if not mostrar_unused:
        df_filtrado = df_filtrado[df_filtrado['type'] != 'UNUSED']
    
    # Exibir estatísticas sobre os filtros
    st.markdown(f"**Mostrando {len(df_filtrado)} de {len(df)} dispositivos.**")
    
    # Mostrar dataframe filtrado
    st.dataframe(df_filtrado)
    
    # Adicionar análises e visualizações
    if not df_filtrado.empty:
        # Contagem por laço
        st.subheader("Distribuição por Laço")
        contagem_laco = df_filtrado['laco'].value_counts()
        st.bar_chart(contagem_laco)
        
        # Contagem por tipo
        st.subheader("Distribuição por Tipo")
        contagem_tipo = df_filtrado['type'].value_counts()
        st.bar_chart(contagem_tipo)
        
        # Contagem por ação
        if 'action' in df_filtrado.columns and not df_filtrado['action'].isnull().all():
            st.subheader("Distribuição por Ação")
            contagem_acao = df_filtrado['action'].value_counts()
            st.bar_chart(contagem_acao)

def pagina_upload(cliente):
    st.subheader(f"Upload de Dados - {cliente}")
    st.write("Escolha o tipo de arquivo para upload:")

    # Criar abas para os diferentes tipos de upload
    tab1, tab2, tab3, tab4 = st.tabs(["TrueService", "TrueAlarm", "Dispositivos", "Histórico Geral"])
    
    with tab1:
        st.markdown("### Log TrueService")
        arquivo_ts = st.file_uploader("Upload .csv/.txt (TrueService)", type=["csv", "txt"], key="ts")
        if arquivo_ts:
            df_ts = pd.read_csv(arquivo_ts, sep=None, engine='python')
            st.dataframe(df_ts.head())
            if st.button("Salvar TrueService no banco", key="save_ts"):
                st.success("Dados TrueService salvos! (simulado)")
    
    with tab2:
        st.markdown("### Log TrueAlarm")
        arquivo_ta = st.file_uploader("Upload .csv/.txt (TrueAlarm)", type=["csv", "txt"], key="ta")
        if arquivo_ta:
            df_ta = pd.read_csv(arquivo_ta, sep=None, engine='python')
            st.dataframe(df_ta.head())
            if st.button("Salvar TrueAlarm no banco", key="save_ta"):
                st.success("Dados TrueAlarm salvos! (simulado)")
    
    with tab3:
        st.markdown("### Lista de Dispositivos")
        arquivo_disp = st.file_uploader("Upload .csv/.txt (Lista de Dispositivos)", type=["csv", "txt"], key="disp")
        if arquivo_disp:
            try:
                # Processar arquivo com função específica para lista de pontos
                df_processado = processamento.processar_arquivo_pontos(arquivo_disp)
                
                # Mostrar dados processados
                st.success(f"Arquivo processado com sucesso! Todos os {len(df_processado)} dispositivos foram carregados, incluindo UNUSED.")
                st.dataframe(df_processado)
                
                # Adicionar análises
                if not df_processado.empty:
                    # Enriquecer dados
                    df_enriquecido = processamento.enriquecer_dados(df_processado)
                    
                    # Mostrar distribuição por tipo
                    st.subheader("Distribuição por Tipo")
                    contagem_tipo = df_processado['type'].value_counts()
                    st.bar_chart(contagem_tipo)
                
                # Botão para salvar no banco
                if st.button("Salvar no banco", key="save_disp"):
                    try:
                        # Salvar no banco
                        db.salvar_pontos(cliente, df_processado)
                        st.success(f"Dados salvos com sucesso na tabela lista_de_pontos para o cliente {cliente}!")
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {str(e)}")
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")
    
    with tab4:
        st.markdown("### Histórico Geral")
        arquivo_hist = st.file_uploader("Upload .csv/.txt (Histórico Geral)", type=["csv", "txt"], key="hist")
        if arquivo_hist:
            df_hist = pd.read_csv(arquivo_hist, sep=None, engine='python')
            st.dataframe(df_hist.head())
            if st.button("Salvar Histórico Geral no banco", key="save_hist"):
                st.success("Dados de Histórico Geral salvos! (simulado)")

def pagina_plano_manutencao(cliente):
    st.subheader(f"Plano de Manutenção - {cliente}")
    
    # Adicionar verificação do estado atual do plano (depuração)
    estado_plano = db.verificar_estado_plano(cliente)
    with st.expander("Informações de depuração do banco de dados"):
        st.write("Estado do plano no banco de dados:")
        st.json(estado_plano)
    
    # Buscar dados do banco de dados
    dados = db.buscar_pontos(cliente)
    
    if not dados:
        st.info(f"Nenhum dispositivo cadastrado para {cliente}. Use a página de Upload para adicionar.")
        return
    
    # Mostrar dados em DataFrame
    df = pd.DataFrame(dados)
    
    # Filtrar excluindo dispositivos com action="ISO" e type="UNUSED"
    df = df[(df['action'] != 'ISO') & (df['type'] != 'UNUSED')]
    
    # Extrair informação de laço
    df['laco'] = df['id_disp'].apply(extrair_laco)
    
    # Definir meses
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", 
        "Maio", "Junho", "Julho", "Agosto", 
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    # Verificar se já existe um plano de manutenção
    plano_existente = db.buscar_plano_manutencao(cliente)
    
    # Se existe, mesclar com os dados
    if plano_existente:
        # Converter para DataFrame
        df_plano = pd.DataFrame(plano_existente)
        # Mesclar com os dados dos dispositivos
        if not df_plano.empty:
            df = pd.merge(df, df_plano[['id_disp', 'mes_manutencao']], on='id_disp', how='left')
        
    # Se não existe ou se faltam dispositivos, inicializamos com mês 0 (não definido)
    if 'mes_manutencao' not in df.columns or df['mes_manutencao'].isnull().any():
        if 'mes_manutencao' not in df.columns:
            df['mes_manutencao'] = 0  # 0 significa não atribuído
        else:
            df['mes_manutencao'] = df['mes_manutencao'].fillna(0)
    
    # Escolher estratégia de distribuição
    st.subheader("Definir Plano de Manutenção")
    
    # Explicação
    st.markdown("""
    Escolha como você deseja distribuir os dispositivos ao longo do ano:
    - **Mensal**: Divide os dispositivos igualmente entre os 12 meses (visitas mensais)
    - **Trimestral**: Divide os dispositivos em 4 grupos (visitas a cada 3 meses)
    - **Semestral**: Divide os dispositivos em 2 grupos (visitas a cada 6 meses)
    - **Anual**: Todos os dispositivos serão testados em janeiro (uma visita por ano)
    """)
    
    # Botões para selecionar estratégia - lado a lado
    col1, col2, col3, col4 = st.columns(4)
    
    estrategia = None
    with col1:
        if st.button("Mensal", use_container_width=True):
            estrategia = "Mensal"
    with col2:
        if st.button("Trimestral", use_container_width=True):
            estrategia = "Trimestral"
    with col3:
        if st.button("Semestral", use_container_width=True):
            estrategia = "Semestral"
    with col4:
        if st.button("Anual", use_container_width=True):
            estrategia = "Anual"
    
    # Botão para aplicar distribuição
    if estrategia:
        st.write(f"Estratégia selecionada: **{estrategia}**")
        
        # Determinar meses de acordo com a estratégia
        if estrategia == "Mensal":
            meses_disponiveis = list(range(1, 13))  # 1 a 12
        elif estrategia == "Trimestral":
            meses_disponiveis = [1, 4, 7, 10]  # Jan, Abr, Jul, Out
        elif estrategia == "Semestral":
            meses_disponiveis = [1, 7]  # Jan, Jul
        else:  # Anual
            meses_disponiveis = [1]  # Janeiro
        
        # Calcular quantidade de dispositivos por mês
        total_dispositivos = len(df)
        qtd_por_mes = {}
        
        # Distribuir igualmente
        dispositivos_por_mes = total_dispositivos // len(meses_disponiveis)
        extras = total_dispositivos % len(meses_disponiveis)
        
        for i, mes in enumerate(meses_disponiveis):
            qtd_por_mes[mes] = dispositivos_por_mes
            if i < extras:
                qtd_por_mes[mes] += 1
        
        # Ordenar dispositivos por laço para manter dispositivos do mesmo laço juntos
        df = df.sort_values(['laco', 'id_disp'])
        
        # Distribuir
        indice_atual = 0
        for mes, quantidade in qtd_por_mes.items():
            # Atribuir mês a cada dispositivo nesse grupo
            for i in range(quantidade):
                if indice_atual < len(df):
                    df.iloc[indice_atual, df.columns.get_loc('mes_manutencao')] = mes
                    indice_atual += 1
        
        # Mensagem de sucesso
        st.success(f"Dispositivos distribuídos conforme estratégia {estrategia}!")
        
        # SALVAR AUTOMATICAMENTE APÓS DISTRIBUIÇÃO
        df_para_salvar = df[df['mes_manutencao'] > 0][['id_disp', 'mes_manutencao']]
        if not df_para_salvar.empty:
            try:
                resultado = db.salvar_plano_manutencao(cliente, df_para_salvar)
                if resultado:
                    st.session_state['plano_salvo'] = True
                    st.success("Plano de manutenção salvo automaticamente no banco de dados!")
                else:
                    st.error("Erro ao salvar o plano automaticamente.")
            except Exception as e:
                st.error(f"Erro ao salvar plano: {str(e)}")
    
    st.subheader("Dispositivos por Mês")
    
    # Criar abas para cada mês
    if 'mes_manutencao' in df.columns:
        tabs = st.tabs(meses)
        
        for i, mes_nome in enumerate(meses):
            mes_numero = i + 1
            with tabs[i]:
                # Destaque visual para o mês atual
                import datetime
                mes_atual = datetime.datetime.now().month
                if mes_numero == mes_atual:
                    st.markdown(f"## {mes_nome} (Mês Atual)")
                else:
                    st.markdown(f"## {mes_nome}")
                    
                df_mes = df[df['mes_manutencao'] == mes_numero]
                
                if not df_mes.empty:
                    st.markdown(f"### {len(df_mes)} dispositivos para testar em {mes_nome}")
                    
                    # Mostrar dispositivos
                    st.dataframe(df_mes[['id_disp', 'type', 'action', 'description', 'laco']])
                    
                    # Mostrar distribuição por laço
                    st.subheader("Dispositivos por Laço")
                    contagem_laco = df_mes['laco'].value_counts()
                    st.bar_chart(contagem_laco)
                else:
                    st.info(f"Nenhum dispositivo programado para {mes_nome}")
             
    # Opções de configuração manual
    st.markdown("---")
    st.subheader("Ajustes Manuais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Selecionar dispositivos")
        
        # Filtro para seleção de dispositivos
        lacos_unicos = sorted(df['laco'].unique())
        laco_selecionado = st.multiselect("Selecionar por Laço:", lacos_unicos)
        
        # Filtrar apenas os dispositivos do laço selecionado
        df_ajuste = df.copy()
        if laco_selecionado:
            df_ajuste = df_ajuste[df_ajuste['laco'].isin(laco_selecionado)]
        
        # Seleção de tipo de dispositivo
        tipos_unicos = sorted(df_ajuste['type'].unique())
        tipo_selecionado = st.multiselect("Selecionar por Tipo:", tipos_unicos)
        
        # Filtrar por tipo selecionado
        if tipo_selecionado:
            df_ajuste = df_ajuste[df_ajuste['type'].isin(tipo_selecionado)]
        
        # Exibir quantidade de dispositivos selecionados
        st.info(f"Selecionados: {len(df_ajuste)} dispositivos")
        
        # Selecionar mês para atribuir
        mes_para_atribuir = st.selectbox(
            "Mês para manutenção:", 
            range(len(meses)),
            format_func=lambda i: meses[i]
        ) + 1  # Ajuste para 1-12
        
        # Botão para aplicar
        if st.button("Atribuir mês aos dispositivos selecionados"):
            for idx in df_ajuste.index:
                df.at[idx, 'mes_manutencao'] = mes_para_atribuir
                 
            st.success(f"{len(df_ajuste)} dispositivos atribuídos para manutenção em {meses[mes_para_atribuir-1]}! Você pode verificar nas abas acima.")
    
    with col2:
        st.markdown("### Visão geral do plano")
        
        # Calcular distribuição por mês
        contagem_por_mes = df['mes_manutencao'].value_counts().sort_index()
        contagem_por_mes = contagem_por_mes[contagem_por_mes.index != 0]  # Excluir não atribuídos
        if not contagem_por_mes.empty:
            # Criar DataFrame para o gráfico
            meses_df = pd.DataFrame({
                'Mês': [meses[i-1] for i in contagem_por_mes.index],
                'Quantidade': contagem_por_mes.values
            })
            # Exibir gráfico
            st.bar_chart(meses_df.set_index('Mês'))
            
            # Mostrar quantos dispositivos não têm mês atribuído
            nao_atribuidos = len(df[df['mes_manutencao'] == 0])
            if nao_atribuidos > 0:
                st.warning(f"{nao_atribuidos} dispositivos ainda não têm mês de manutenção atribuído.")
        else:
            st.info("Nenhum dispositivo tem mês de manutenção atribuído ainda.")
        
        # Resumo da distribuição
        st.markdown("### Resumo da distribuição:")
        for i, mes_nome in enumerate(meses):
            mes_numero = i + 1
            qtd = len(df[df['mes_manutencao'] == mes_numero])
            if qtd > 0:
                st.markdown(f"**{mes_nome}:** {qtd} dispositivos")
        
        # Salvar o plano de manutenção no banco
        if st.button("Salvar Plano de Manutenção"):
            # Preparar DataFrame para salvar
            # Filtrar dispositivos com mês atribuído
            df_para_salvar = df[df['mes_manutencao'] > 0][['id_disp', 'mes_manutencao']]
            
            if df_para_salvar.empty:
                st.error("Nenhum dispositivo tem mês de manutenção atribuído. Distribua os dispositivos primeiro.")
                return
            
            # Debug: mostrar o que está sendo salvo
            with st.expander("Dados a serem salvos"):
                st.dataframe(df_para_salvar)
            
            # Salvar no banco
            resultado = db.salvar_plano_manutencao(cliente, df_para_salvar)
            
            if resultado:
                # Force um refresh após salvar
                st.session_state['plano_salvo'] = True
                st.success("Plano de manutenção salvo com sucesso!")
            else:
                st.error("Erro ao salvar o plano de manutenção.")

def pagina_saude_sistema(cliente):
    st.title("Saúde do Sistema")
    st.subheader(f"Cliente: {cliente}")
    
    # Seletor de mês e ano
    col1, col2, col3 = st.columns(3)
    with col1:
        ano = st.selectbox("Ano", list(range(datetime.now().year - 2, datetime.now().year + 1)))
    with col2:
        mostrar_mes_especifico = st.checkbox("Filtrar por mês específico", value=False)
    
    mes = None
    if mostrar_mes_especifico:
        with col3:
            mes = st.selectbox("Mês", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
    
    # Buscar dispositivos planejados para todo o ANO
    dispositivos_planejados_ano = buscar_manutencao_anual(cliente, ano)
    
    # Filtrar por mês se solicitado
    if mostrar_mes_especifico and mes is not None:
        dispositivos_planejados = [d for d in dispositivos_planejados_ano if d['mes'] == mes]
        # Buscar testes apenas do mês selecionado
        testes_anteriores = buscar_testes_dispositivos(cliente, mes, ano)
    else:
        dispositivos_planejados = dispositivos_planejados_ano
        # Para testes de todos os meses, teríamos que combinar os resultados de cada mês
        testes_anteriores = []
        for m in range(1, 13):
            testes_mes = buscar_testes_dispositivos(cliente, m, ano)
            testes_anteriores.extend(testes_mes)
    
    # Buscar ações corretivas
    if mostrar_mes_especifico and mes is not None:
        acoes_corretivas = buscar_acoes_corretivas(cliente, mes, ano)
    else:
        acoes_corretivas = buscar_acoes_corretivas(cliente, None, ano)
    
    # RESUMO GERAL
    st.header(f"Resumo do Sistema - {ano}" + (f" - {calendar.month_name[mes]}" if mostrar_mes_especifico and mes else ""))
    
    # Total de dispositivos planejados para o ano/mês
    total_dispositivos_planejados = len(dispositivos_planejados)
    
    # Se não há dispositivos planejados
    if total_dispositivos_planejados == 0:
        st.warning(f"Não há dispositivos planejados para manutenção" + 
                  (f" em {calendar.month_name[mes]}" if mostrar_mes_especifico and mes else " neste ano"))
        return
    
    # Converter testes para DataFrame para facilitar análise
    if testes_anteriores:
        df_testes = pd.DataFrame(testes_anteriores)
        
        # Calcular métricas
        testes_realizados = len(df_testes)
        testes_ok = len(df_testes[df_testes['status'] == 'Teste OK'])
        testes_nok = len(df_testes[df_testes['status'] == 'Teste Não OK'])
    else:
        testes_realizados = 0
        testes_ok = 0
        testes_nok = 0
    
    # Métricas de ações corretivas
    acoes_total = len(acoes_corretivas)
    acoes_resolvidas = len([a for a in acoes_corretivas if a['resolvido']])
    acoes_pendentes = acoes_total - acoes_resolvidas
    
    # Exibir métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Dispositivos Planejados", total_dispositivos_planejados)
    with col2:
        st.metric("Testes Realizados", testes_realizados)
    with col3:
        st.metric("Testes OK", testes_ok)
    with col4:
        st.metric("Testes Não OK", testes_nok)
    with col5:
        st.metric("Ações Pendentes", acoes_pendentes)
    
    # Gráfico de pizza para visualizar os resultados dos testes
    if testes_realizados > 0 and total_dispositivos_planejados > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribuição dos Testes")
            data = {
                'Status': ['Teste OK', 'Teste Não OK', 'Não Testados'],
                'Quantidade': [testes_ok, testes_nok, total_dispositivos_planejados - testes_realizados]
            }
            df_grafico = pd.DataFrame(data)
            fig = px.pie(df_grafico, names='Status', values='Quantidade', 
                        color='Status', 
                        color_discrete_map={
                            'Teste OK': 'green',
                            'Teste Não OK': 'red',
                            'Não Testados': 'gray'
                        })
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico para ações corretivas
        if acoes_total > 0:
            with col2:
                st.subheader("Status das Ações Corretivas")
                data = {
                    'Status': ['Resolvidas', 'Pendentes'],
                    'Quantidade': [acoes_resolvidas, acoes_pendentes]
                }
                df_grafico = pd.DataFrame(data)
                fig = px.pie(df_grafico, names='Status', values='Quantidade', 
                            color='Status', 
                            color_discrete_map={
                                'Resolvidas': 'green',
                                'Pendentes': 'orange'
                            })
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
    
    # DISTRIBUIÇÃO POR MÊS
    if not mostrar_mes_especifico:
        st.header("Distribuição Mensal de Manutenções")
        
        # Contar dispositivos por mês
        dispositivos_por_mes = {}
        for disp in dispositivos_planejados_ano:
            mes = disp['mes']
            if mes not in dispositivos_por_mes:
                dispositivos_por_mes[mes] = 0
            dispositivos_por_mes[mes] += 1
        
        # Criar DataFrame para gráfico
        meses_df = []
        for m in range(1, 13):
            total_mes = dispositivos_por_mes.get(m, 0)
            if total_mes > 0:
                meses_df.append({
                    'Mês': calendar.month_name[m],
                    'Dispositivos': total_mes
                })
        
        if meses_df:
            df_meses = pd.DataFrame(meses_df)
            fig = px.bar(df_meses, x='Mês', y='Dispositivos', 
                        title="Dispositivos para manutenção por mês",
                        color='Dispositivos')
            st.plotly_chart(fig, use_container_width=True)
    
    # AÇÕES CORRETIVAS
    if acoes_corretivas:
        st.header("Histórico de Ações Corretivas")
        
        # Converter para DataFrame
        df_acoes = pd.DataFrame(acoes_corretivas)
        
        # Obter dispositivos do cliente para mostrar descrições
        df_disp = obter_dispositivos(cliente)
        df_disp = df_disp.rename(columns={'id': 'id_disp'})
        
        # Mesclar para obter descrições dos dispositivos
        if not df_disp.empty and not df_acoes.empty:
            df_acoes = pd.merge(
                df_acoes,
                df_disp[['id_disp', 'descricao']],
                on='id_disp',
                how='left'
            )
        
        # Formatar data de registro
        if 'data_registro' in df_acoes.columns:
            df_acoes['data_registro'] = pd.to_datetime(df_acoes['data_registro'])
            df_acoes['data_formatada'] = df_acoes['data_registro'].dt.strftime('%d/%m/%Y %H:%M')
        
        # Mostrar em formato expandido
        for i, acao in df_acoes.iterrows():
            resolvido_status = "✅ Resolvido" if acao['resolvido'] else "⏳ Pendente"
            with st.expander(f"**{acao['id_disp']}** - {acao.get('descricao', 'Dispositivo')} ({resolvido_status})"):
                st.write(f"**Problema:** {acao['descricao_problema']}")
                st.write(f"**Ação Corretiva:** {acao['acao_corretiva']}")
                st.write(f"**Data:** {acao.get('data_formatada', 'N/A')}")
                st.write(f"**Mês/Ano:** {calendar.month_name[acao['mes']]}/{acao['ano']}")
    else:
        st.info("Não há ações corretivas registradas para este período")
    
    # Visão histórica (gráfico de tendência)
    st.header("Histórico de Manutenção")
    st.info("Histórico de manutenção em desenvolvimento")

def pagina_manutencao_mensal(cliente):
    st.title("Relatório de Manutenção Mensal")
    
    # Selecionar apenas mês e ano (cliente já está definido pelo menu)
    col1, col2 = st.columns(2)
    with col1:
        mes = st.selectbox("Mês", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
    with col2:
        ano = st.selectbox("Ano", list(range(datetime.now().year - 2, datetime.now().year + 1)))
    
    st.subheader(f"Cliente: {cliente}")
    
    # Obter dispositivos programados para este mês específico
    dispositivos_planejados = buscar_manutencao_mensal(cliente, mes)
    
    if not dispositivos_planejados:
        st.warning(f"Não há dispositivos programados para manutenção em {calendar.month_name[mes]} para o cliente {cliente}")
        return
    
    # Obter todos os dispositivos para referência e converter para DataFrame
    df_disp = obter_dispositivos(cliente)
    
    # Filtrar apenas os dispositivos planejados para o mês
    ids_planejados = [disp['id_disp'] for disp in dispositivos_planejados]
    df_disp_mes = df_disp[df_disp['id'].isin(ids_planejados)]
    
    # Obter testes já realizados
    testes_anteriores = buscar_testes_dispositivos(cliente, mes, ano)
    
    # Construir relatório
    with st.container():
        st.header(f"Relatório para {cliente} - {calendar.month_name[mes]} de {ano}")
        
        # Métricas principais
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Dispositivos Planejados", len(df_disp_mes))
        with col2:
            testes_realizados = len([t for t in testes_anteriores if t['status'] != ''])
            percentual = (testes_realizados / len(df_disp_mes) * 100) if len(df_disp_mes) > 0 else 0
            st.metric("Testes Realizados", f"{percentual:.1f}%")
    
    # Botão para exportar dados
    if st.download_button(
        label="📊 Exportar Dados do Mês",
        data=get_csv_download_data(df_disp_mes, testes_anteriores),
        file_name=f'relatorio_{cliente}_{calendar.month_name[mes]}_{ano}.csv',
        mime='text/csv',
    ):
        st.success("Dados exportados com sucesso!")
    
    # Seção para checklist de testes
    st.header("Checklist de Testes")
    st.markdown("Registre abaixo os resultados dos testes para cada dispositivo:")
    
    # Criar DataFrame para os resultados dos testes (apenas dispositivos planejados para o mês)
    df_testes = pd.DataFrame(df_disp_mes[['id', 'descricao']])
    df_testes.rename(columns={'id': 'id_disp'}, inplace=True)
    df_testes['status'] = ''
    df_testes['observacao'] = ''
    
    # Preencher com testes anteriores, se existirem
    testes_dict = {teste['id_disp']: teste for teste in testes_anteriores}
    for idx, row in df_testes.iterrows():
        id_disp = row['id_disp']
        if id_disp in testes_dict:
            df_testes.at[idx, 'status'] = testes_dict[id_disp].get('status', '')
            df_testes.at[idx, 'observacao'] = testes_dict[id_disp].get('observacao', '')
    
    # Criar layout da tabela de testes
    for i, row in df_testes.iterrows():
        col1, col2, col3, col4 = st.columns([1, 2, 2, 3])
        with col1:
            st.text(row['id_disp'])
        with col2:
            st.text(row['descricao'])
        with col3:
            status_key = f"status_{row['id_disp']}"
            status_atual = row['status']
            status_opcoes = ["", "Teste OK", "Teste Não OK"]
            df_testes.at[i, 'status'] = st.selectbox(
                "Status",
                options=status_opcoes,
                index=status_opcoes.index(status_atual) if status_atual in status_opcoes else 0,
                key=status_key,
                label_visibility="collapsed"
            )
        with col4:
            obs_key = f"obs_{row['id_disp']}"
            df_testes.at[i, 'observacao'] = st.text_input(
                "Observação",
                value=row['observacao'],
                key=obs_key,
                label_visibility="collapsed"
            )
    
    # Botão para salvar os testes
    if st.button("Salvar Resultados dos Testes"):
        # Filtramos apenas os testes com status
        df_para_salvar = df_testes[df_testes['status'] != ''].copy()
        
        if df_para_salvar.empty:
            st.warning("Nenhum resultado de teste para salvar.")
        else:
            sucesso = salvar_teste_dispositivos(cliente, mes, ano, df_para_salvar)
            if sucesso:
                st.success("Resultados dos testes salvos com sucesso!")
            else:
                st.error("Erro ao salvar os resultados dos testes.")
    
    # Seção de Ações Corretivas - mostra dispositivos com problemas
    if testes_anteriores:
        # Filtrar apenas os testes com problemas (status "Teste Não OK")
        problemas = [t for t in testes_anteriores if t.get('status') == 'Teste Não OK']
        
        if problemas:
            st.header("Ações Corretivas Necessárias")
            st.warning(f"{len(problemas)} dispositivos requerem ações corretivas")
            
            # Variável para controlar se alguma ação foi salva
            acoes_salvas = False
            
            for problema in problemas:
                id_disp = problema['id_disp']
                observacao = problema['observacao']
                
                # Buscar descrição do dispositivo
                descricao = "Sem descrição"
                dispositivo = df_disp[df_disp['id'] == id_disp]
                if not dispositivo.empty:
                    descricao = dispositivo.iloc[0]['descricao']
                
                # Exibir detalhes do problema
                with st.expander(f"**{id_disp}** - {descricao}"):
                    st.write(f"**Problema relatado:** {observacao}")
                    
                    # Campo para ação corretiva
                    acao = st.text_area(
                        f"Ação corretiva para {id_disp}", 
                        key=f"acao_{id_disp}", 
                        placeholder="Descreva a ação corretiva a ser tomada..."
                    )
                    
                    # Opções para marcar resolução
                    resolvido = st.checkbox("Problema resolvido", key=f"resolvido_{id_disp}")
                    
                    # Botão para salvar a ação corretiva no banco
                    if st.button("Registrar Ação", key=f"btn_{id_disp}"):
                        if not acao:
                            st.error("Por favor, descreva a ação corretiva antes de registrar.")
                        else:
                            # Salvar no banco de dados
                            salvo = salvar_acao_corretiva(
                                cliente, mes, ano, id_disp, 
                                observacao, acao, resolvido
                            )
                            
                            if salvo:
                                st.success(f"Ação corretiva registrada para {id_disp}")
                                acoes_salvas = True
                            else:
                                st.error("Erro ao registrar ação corretiva")
            
            # Mostrar mensagem se ações foram salvas
            if acoes_salvas:
                st.success("Ações corretivas registradas com sucesso!")
                
    # Nota informativa sobre onde ver os resumos
    st.info("Para visualizar o resumo completo dos testes e análise de saúde do sistema, acesse a página 'Saúde do Sistema' no menu lateral.")

def get_csv_download_data(df_dispositivos, testes):
    """
    Prepara dados para download como CSV
    
    Parâmetros:
    df_dispositivos: DataFrame com informações dos dispositivos
    testes: Lista de dicionários com resultados dos testes
    
    Retorna:
    str: Conteúdo CSV formatado
    """
    # Converter testes para DataFrame
    if testes:
        df_testes = pd.DataFrame(testes)
    else:
        df_testes = pd.DataFrame(columns=['id_disp', 'status', 'observacao', 'data_teste'])
    
    # Renomear coluna 'id' para 'id_disp' em df_dispositivos para mesclar
    df_dispositivos = df_dispositivos.rename(columns={'id': 'id_disp'})
    
    # Mesclar os DataFrames
    df_resultado = pd.merge(
        df_dispositivos, 
        df_testes,
        on='id_disp',
        how='left'
    )
    
    # Preencher valores nulos
    df_resultado['status'] = df_resultado['status'].fillna('Não Testado')
    df_resultado['observacao'] = df_resultado['observacao'].fillna('')
    
    # Converter para CSV
    return df_resultado.to_csv(index=False)

if __name__ == "__main__":
    main()
