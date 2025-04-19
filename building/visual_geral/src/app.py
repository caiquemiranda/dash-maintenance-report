import streamlit as st
import pandas as pd

# Simulação de clientes cadastrados (depois virá do banco)
CLIENTES = ['BRD', 'BYR', 'AERO', 'BSC']

# Simulação de navegação
MENU_OPCOES = [
    'Histórico Geral',
    'TrueService',
    'TrueAlarm',
    'Lista Dispositivos',
    'Plano de Manutenção',
    'Manutenção Mensal',
    'Saúde do Sistema',
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
    else:
        st.write(f"Página: {opcao} (em construção)")

def pagina_upload(cliente):
    st.subheader(f"Upload de Dados - {cliente}")
    st.write("Escolha o tipo de arquivo para upload:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Log TrueService")
        arquivo_ts = st.file_uploader("Upload .csv/.txt (TrueService)", type=["csv", "txt"], key="ts")
        if arquivo_ts:
            df_ts = pd.read_csv(arquivo_ts, sep=None, engine='python')
            st.dataframe(df_ts.head())
            if st.button("Salvar TrueService no banco", key="save_ts"):
                st.success("Dados TrueService salvos! (simulado)")
        st.markdown("### Dispositivos")
        arquivo_disp = st.file_uploader("Upload .csv/.txt (Dispositivos)", type=["csv", "txt"], key="disp")
        if arquivo_disp:
            df_disp = pd.read_csv(arquivo_disp, sep=None, engine='python')
            st.dataframe(df_disp.head())
            if st.button("Salvar Dispositivos no banco", key="save_disp"):
                st.success("Dados de Dispositivos salvos! (simulado)")
    with col2:
        st.markdown("### Log TrueAlarm")
        arquivo_ta = st.file_uploader("Upload .csv/.txt (TrueAlarm)", type=["csv", "txt"], key="ta")
        if arquivo_ta:
            df_ta = pd.read_csv(arquivo_ta, sep=None, engine='python')
            st.dataframe(df_ta.head())
            if st.button("Salvar TrueAlarm no banco", key="save_ta"):
                st.success("Dados TrueAlarm salvos! (simulado)")
        st.markdown("### Histórico Geral")
        arquivo_hist = st.file_uploader("Upload .csv/.txt (Histórico Geral)", type=["csv", "txt"], key="hist")
        if arquivo_hist:
            df_hist = pd.read_csv(arquivo_hist, sep=None, engine='python')
            st.dataframe(df_hist.head())
            if st.button("Salvar Histórico Geral no banco", key="save_hist"):
                st.success("Dados de Histórico Geral salvos! (simulado)")

    st.markdown("---")
    st.markdown("Outros tipos de upload podem ser adicionados aqui...")

if __name__ == "__main__":
    main()
