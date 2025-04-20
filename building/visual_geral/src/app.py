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
    
    # Filtrar excluindo dispositivos com action="ISO" e type="UNUSED"
    df = df[(df['action'] != 'ISO') & (df['type'] != 'UNUSED')]
    
    # Extrair informação de laço
    df['laco'] = df['id_disp'].apply(extrair_laco)
    
    # Verificar se já existe um plano de manutenção
    plano_existente = db.buscar_plano_manutencao(cliente)
    
    if plano_existente:
        # Converter para DataFrame
        df_plano = pd.DataFrame(plano_existente)
        # Mesclar com os dados dos dispositivos
        if not df_plano.empty:
            df = pd.merge(df, df_plano[['id_disp', 'periodicidade']], on='id_disp', how='left')
            df['periodicidade'] = df['periodicidade'].fillna(12)  # Padrão: anual
    else:
        # Não existe plano, iniciar com todos como anuais
        df['periodicidade'] = 12
    
    # Dividir por periodicidade
    total_dispositivos = len(df)
    
    # Determinar quantos dispositivos para cada periodicidade
    # Se não houver configuração prévia, dividimos igualmente
    if 'periodicidade' not in df.columns:
        # Cálculo para dividir aproximadamente
        qtd_mensal = total_dispositivos // 12
        qtd_trimestral = total_dispositivos // 4
        qtd_semestral = total_dispositivos // 2
        qtd_anual = total_dispositivos - qtd_mensal - qtd_trimestral - qtd_semestral
        
        # Distribuir
        df = df.sort_values('id_disp')
        df['periodicidade'] = 12  # Padrão: anual
        
        if qtd_mensal > 0:
            df.iloc[:qtd_mensal, df.columns.get_loc('periodicidade')] = 1
        if qtd_trimestral > 0:
            df.iloc[qtd_mensal:qtd_mensal+qtd_trimestral, df.columns.get_loc('periodicidade')] = 3
        if qtd_semestral > 0:
            df.iloc[qtd_mensal+qtd_trimestral:qtd_mensal+qtd_trimestral+qtd_semestral, df.columns.get_loc('periodicidade')] = 6
    
    # Separar por periodicidade
    df_mensal = df[df['periodicidade'] == 1]
    df_trimestral = df[df['periodicidade'] == 3]
    df_semestral = df[df['periodicidade'] == 6]
    df_anual = df[df['periodicidade'] == 12]
    
    # Exibir em abas
    tab1, tab2, tab3, tab4 = st.tabs(["Mensal (1 mês)", "Trimestral (3 meses)", "Semestral (6 meses)", "Anual (12 meses)"])
    
    with tab1:
        st.write(f"### Dispositivos com manutenção mensal - {len(df_mensal)} dispositivos")
        if not df_mensal.empty:
            st.dataframe(df_mensal[['id_disp', 'type', 'action', 'description', 'laco', 'periodicidade']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_mensal['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção mensal.")
    
    with tab2:
        st.write(f"### Dispositivos com manutenção trimestral - {len(df_trimestral)} dispositivos")
        if not df_trimestral.empty:
            st.dataframe(df_trimestral[['id_disp', 'type', 'action', 'description', 'laco', 'periodicidade']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_trimestral['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção trimestral.")
    
    with tab3:
        st.write(f"### Dispositivos com manutenção semestral - {len(df_semestral)} dispositivos")
        if not df_semestral.empty:
            st.dataframe(df_semestral[['id_disp', 'type', 'action', 'description', 'laco', 'periodicidade']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_semestral['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção semestral.")
    
    with tab4:
        st.write(f"### Dispositivos com manutenção anual - {len(df_anual)} dispositivos")
        if not df_anual.empty:
            st.dataframe(df_anual[['id_disp', 'type', 'action', 'description', 'laco', 'periodicidade']])
            
            # Gráfico distribuição por laço
            st.subheader("Dispositivos por Laço")
            contagem_laco = df_anual['laco'].value_counts()
            st.bar_chart(contagem_laco)
        else:
            st.info("Não há dispositivos com manutenção anual.")
            
    # Opções de configuração manual
    st.markdown("---")
    st.subheader("Configurar Plano de Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Ajustar periodicidade")
        
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
        
        # Opção para atribuir periodicidade
        nova_periodicidade = st.selectbox("Definir periodicidade:", [
            ("Mensal", 1),
            ("Trimestral", 3),
            ("Semestral", 6),
            ("Anual", 12)
        ], format_func=lambda x: x[0])
        
        # Botão para aplicar
        if st.button("Aplicar periodicidade"):
            for idx in df_ajuste.index:
                df.at[idx, 'periodicidade'] = nova_periodicidade[1]
            st.success(f"Periodicidade {nova_periodicidade[0]} aplicada a {len(df_ajuste)} dispositivos!")
    
    with col2:
        st.markdown("### Distribuição atual")
        
        # Criar dicionário para contagem de periodicidades
        contagem_periodicidade = {
            1: len(df_mensal),    # Mensal
            3: len(df_trimestral), # Trimestral
            6: len(df_semestral),  # Semestral
            12: len(df_anual)      # Anual
        }
        
        # Criar DataFrame com as contagens (garantindo que todos os valores estejam presentes)
        periodicidade_df = pd.DataFrame({
            'Periodicidade': ['Mensal', 'Trimestral', 'Semestral', 'Anual'],
            'Quantidade': [contagem_periodicidade[1], contagem_periodicidade[3], 
                          contagem_periodicidade[6], contagem_periodicidade[12]]
        })
        
        # Exibir como gráfico de barras
        st.bar_chart(periodicidade_df.set_index('Periodicidade'))
        
        # Mostrar quantidade de cada periodicidade e porcentagem
        st.markdown(f"**Mensal:** {len(df_mensal)} dispositivos ({len(df_mensal)/len(df)*100:.1f}%)")
        st.markdown(f"**Trimestral:** {len(df_trimestral)} dispositivos ({len(df_trimestral)/len(df)*100:.1f}%)")
        st.markdown(f"**Semestral:** {len(df_semestral)} dispositivos ({len(df_semestral)/len(df)*100:.1f}%)")
        st.markdown(f"**Anual:** {len(df_anual)} dispositivos ({len(df_anual)/len(df)*100:.1f}%)")
        
        # Salvar o plano de manutenção no banco
        if st.button("Salvar Plano de Manutenção"):
            # Preparar DataFrame para salvar
            plano_df = df[['id_disp', 'periodicidade']]
            
            # Salvar no banco
            resultado = db.salvar_plano_manutencao(cliente, plano_df)
            
            if resultado:
                st.success("Plano de manutenção salvo com sucesso!")
            else:
                st.error("Erro ao salvar o plano de manutenção.")

def pagina_manutencao_mensal(cliente):
    st.subheader(f"Manutenção Mensal - {cliente}")
    
    # Verificar se existe um plano de manutenção salvo
    plano_existente = db.buscar_plano_manutencao(cliente)
    
    if not plano_existente:
        st.warning(f"Nenhum plano de manutenção definido para {cliente}. Vá para a página 'Plano de Manutenção' para configurar.")
        return
    
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
    
    # Buscar as manutenções do mês
    manutencoes_do_mes = db.buscar_manutencao_mensal(cliente, mes_numero)
    
    # Converter para DataFrame para facilitar operações
    if manutencoes_do_mes:
        df_testar = pd.DataFrame(manutencoes_do_mes)
        # Extrair informação de laço
        df_testar['laco'] = df_testar['id_disp'].apply(extrair_laco)
    else:
        df_testar = pd.DataFrame()
    
    if not df_testar.empty:
        st.success(f"Para o mês de {mes_selecionado}, você precisa testar {len(df_testar)} dispositivos!")
        
        # Filtro por laço
        lacos_unicos = sorted(df_testar['laco'].unique())
        laco_selecionado = st.multiselect("Filtrar por Laço:", lacos_unicos)
        
        # Aplicar filtro
        if laco_selecionado:
            df_testar = df_testar[df_testar['laco'].isin(laco_selecionado)]
        
        # Exibir tabela
        st.dataframe(df_testar[['id_disp', 'type', 'action', 'description', 'laco']])
        
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
