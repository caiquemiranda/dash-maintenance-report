import streamlit as st
import pandas as pd
import os
import sys

# Importar módulos criados
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import db
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
    
    # Buscar dados do banco de dados
    dados = db.buscar_pontos(cliente)
    
    if not dados:
        st.info(f"Nenhum dispositivo cadastrado para {cliente}. Use a página de Upload para adicionar.")
        return
    
    # Mostrar dados em DataFrame
    df = pd.DataFrame(dados)
    
    # Filtrar excluindo dispositivos com action="ISO"
    df = df[df['action'] != 'ISO']
    
    # Extrair informação de laço
    df['laco'] = df['id_disp'].apply(extrair_laco)
    
    # Determinar o período de manutenção baseado no type
    def determinar_periodo(row):
        tipo = row['type'].upper() if isinstance(row['type'], str) else ""
        
        # Dispositivos que precisam de manutenção bimestral (a cada 2 meses)
        if tipo in ['MBZAM', 'IAM', 'ADRPUL']:
            return 2
        # Dispositivos que precisam de manutenção quadrimestral (a cada 4 meses)
        elif tipo in ['PHOTO', 'IDNETISO']:
            return 4
        # Outros dispositivos com manutenção anual
        else:
            return 12
    
    df['periodo_manutencao'] = df.apply(determinar_periodo, axis=1)
    
    # Dividir por períodos
    df_bimestral = df[df['periodo_manutencao'] == 2]
    df_quadrimestral = df[df['periodo_manutencao'] == 4]
    df_anual = df[df['periodo_manutencao'] == 12]
    
    # Exibir em abas
    tab1, tab2, tab3 = st.tabs(["Bimestral (2 meses)", "Quadrimestral (4 meses)", "Anual (12 meses)"])
    
    with tab1:
        st.write(f"### Dispositivos com manutenção a cada 2 meses - {len(df_bimestral)} dispositivos")
        if not df_bimestral.empty:
            st.dataframe(df_bimestral[['id_disp', 'type', 'action', 'description', 'laco']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_bimestral['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção bimestral.")
    
    with tab2:
        st.write(f"### Dispositivos com manutenção a cada 4 meses - {len(df_quadrimestral)} dispositivos")
        if not df_quadrimestral.empty:
            st.dataframe(df_quadrimestral[['id_disp', 'type', 'action', 'description', 'laco']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_quadrimestral['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção quadrimestral.")
    
    with tab3:
        st.write(f"### Dispositivos com manutenção anual - {len(df_anual)} dispositivos")
        if not df_anual.empty:
            st.dataframe(df_anual[['id_disp', 'type', 'action', 'description', 'laco']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_anual['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção anual.")

def pagina_manutencao_mensal(cliente):
    st.subheader(f"Manutenção Mensal - {cliente}")
    
    # Buscar dados do banco de dados
    dados = db.buscar_pontos(cliente)
    
    if not dados:
        st.info(f"Nenhum dispositivo cadastrado para {cliente}. Use a página de Upload para adicionar.")
        return
    
    # Mostrar dados em DataFrame
    df = pd.DataFrame(dados)
    
    # Filtrar excluindo dispositivos com action="ISO"
    df = df[df['action'] != 'ISO']
    
    # Extrair informação de laço
    df['laco'] = df['id_disp'].apply(extrair_laco)
    
    # Determinar o período de manutenção baseado no type
    def determinar_periodo(row):
        tipo = row['type'].upper() if isinstance(row['type'], str) else ""
        
        # Dispositivos que precisam de manutenção bimestral (a cada 2 meses)
        if tipo in ['MBZAM', 'IAM', 'ADRPUL']:
            return 2
        # Dispositivos que precisam de manutenção quadrimestral (a cada 4 meses)
        elif tipo in ['PHOTO', 'IDNETISO']:
            return 4
        # Outros dispositivos com manutenção anual
        else:
            return 12
    
    df['periodo_manutencao'] = df.apply(determinar_periodo, axis=1)
    
    # Seletor de mês atual
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", 
        "Maio", "Junho", "Julho", "Agosto", 
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    # Obter mês atual como padrão
    import datetime
    mes_atual = datetime.datetime.now().month
    mes_selecionado = st.selectbox("Selecione o mês para verificar os testes", meses, index=mes_atual-1)
    
    # Converter mês selecionado para número (1-12)
    mes_numero = meses.index(mes_selecionado) + 1
    
    # Determinar quais dispositivos devem ser testados neste mês
    def testar_no_mes(row, mes):
        periodo = row['periodo_manutencao']
        
        # Se for bimestral (2), testa nos meses ímpares ou pares
        if periodo == 2:
            return mes % 2 == 1  # meses ímpares: 1,3,5,7,9,11
        
        # Se for quadrimestral (4), testa nos meses 1, 5, 9
        elif periodo == 4:
            return mes in [1, 5, 9]
        
        # Se for anual (12), testa no mês 1 (Janeiro)
        elif periodo == 12:
            return mes == 1
        
        return False
    
    df['testar_este_mes'] = df.apply(lambda row: testar_no_mes(row, mes_numero), axis=1)
    
    # Filtrar apenas dispositivos para testar neste mês
    df_testar = df[df['testar_este_mes']]
    
    if not df_testar.empty:
        st.success(f"Para o mês de {mes_selecionado}, você precisa testar {len(df_testar)} dispositivos!")
        
        # Filtro por laço
        lacos_unicos = sorted(df_testar['laco'].unique())
        laco_selecionado = st.multiselect("Filtrar por Laço:", lacos_unicos)
        
        # Aplicar filtro
        if laco_selecionado:
            df_testar = df_testar[df_testar['laco'].isin(laco_selecionado)]
        
        # Exibir tabela
        st.dataframe(df_testar[['id_disp', 'type', 'action', 'description', 'laco', 'periodo_manutencao']])
        
        # Gráfico distribuição por laço
        st.subheader("Dispositivos por Laço")
        contagem_laco = df_testar['laco'].value_counts()
        st.bar_chart(contagem_laco)
        
        # Gráfico distribuição por tipo
        st.subheader("Dispositivos por Tipo")
        contagem_tipo = df_testar['type'].value_counts()
        st.bar_chart(contagem_tipo)
    else:
        st.info(f"Não há dispositivos para testar no mês de {mes_selecionado}.")

if __name__ == "__main__":
    main()
