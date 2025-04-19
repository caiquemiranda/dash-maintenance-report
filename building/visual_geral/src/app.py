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
    else:
        st.write(f"Página: {opcao} (em construção)")

def pagina_dispositivos(cliente):
    st.subheader(f"Lista de Dispositivos - {cliente}")
    
    # Buscar dados do banco de dados
    dados = db.buscar_pontos(cliente)
    
    if not dados:
        st.info(f"Nenhum dispositivo cadastrado para {cliente}. Use a página de Upload para adicionar.")
        return
    
    # Mostrar dados em DataFrame
    df = pd.DataFrame(dados)
    
    # Adicionar opções de filtro
    st.markdown("### Filtros")
    col1, col2, col3 = st.columns(3)
    
    # Filtro por tipo
    with col1:
        tipos_unicos = sorted(df['type'].unique())
        tipo_selecionado = st.multiselect("Filtrar por Tipo:", tipos_unicos)
    
    # Filtro por texto na descrição
    with col2:
        texto_busca = st.text_input("Buscar na descrição:")
    
    # Opção para mostrar/ocultar UNUSED
    with col3:
        mostrar_unused = st.checkbox("Mostrar UNUSED", value=True)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    # Filtro por tipo
    if tipo_selecionado:
        df_filtrado = df_filtrado[df_filtrado['type'].isin(tipo_selecionado)]
    
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

if __name__ == "__main__":
    main()
