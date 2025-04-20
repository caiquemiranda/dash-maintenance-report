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

def pagina_manutencao_mensal(cliente):
    st.subheader(f"Manutenção Mensal - {cliente}")
    
    # Debug - verificar estado atual do plano
    estado_plano = db.verificar_estado_plano(cliente)
    with st.expander("Informações de depuração do banco de dados"):
        st.write("Estado do plano no banco de dados:")
        st.json(estado_plano)
    
    # Usando método compatível com todas versões do Streamlit
    if 'plano_salvo' in st.session_state and st.session_state['plano_salvo']:
        st.session_state['plano_salvo'] = False
        try:
            # Versões mais recentes
            st.rerun()
        except AttributeError:
            # Versões mais antigas - não tenta recarregar, apenas avisa
            st.info("Para ver as alterações mais recentes, recarregue a página.")
    
    # Verificar se existe um plano de manutenção salvo
    plano_existente = db.buscar_plano_manutencao(cliente)
    
    if not plano_existente:
        st.warning(f"Nenhum plano de manutenção definido para {cliente}. Vá para a página 'Plano de Manutenção' e defina um mês para cada dispositivo.")
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
    if not manutencoes_do_mes:
        st.warning(f"Não há dispositivos para testar em {mes_selecionado}. Verifique se o plano de manutenção está configurado corretamente.")
        df_testar = pd.DataFrame()
    else:
        st.success(f"Para o mês de {mes_selecionado}, você precisa testar {len(manutencoes_do_mes)} dispositivos!")
        df_testar = pd.DataFrame(manutencoes_do_mes)
        # Extrair informação de laço
        df_testar['laco'] = df_testar['id_disp'].apply(extrair_laco)
    
    if not df_testar.empty:
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
