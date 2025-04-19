import streamlit as st
import pandas as pd

# Simulação de clientes cadastrados (depois virá do banco)
CLIENTES = ['Cliente A', 'Cliente B', 'Cliente C']

# Simulação de navegação
MENU_OPCOES = [
    'Histórico Geral',
    'TrueService',
    'TrueAlarm',
    'Lista Dispositivos',
    'Plano de Manutenção',
    'Upload de Dados'
]

def main():
    st.set_page_config(page_title="Dashboard de Manutenção", layout="wide")
    st.title("Dashboard de Manutenção Multi-Cliente")

    # Sidebar: seleção de cliente
    st.sidebar.header("Selecione o Cliente")
    cliente = st.sidebar.selectbox("Cliente", CLIENTES)

    # Sidebar: menu de navegação (aparece só após seleção do cliente)
    if cliente:
        st.sidebar.header("Menu")
        opcao = st.sidebar.radio("Ir para", MENU_OPCOES)
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
    with col2:
        st.markdown("### Log TrueAlarm")
        arquivo_ta = st.file_uploader("Upload .csv/.txt (TrueAlarm)", type=["csv", "txt"], key="ta")
        if arquivo_ta:
            df_ta = pd.read_csv(arquivo_ta, sep=None, engine='python')
            st.dataframe(df_ta.head())
            if st.button("Salvar TrueAlarm no banco", key="save_ta"):
                st.success("Dados TrueAlarm salvos! (simulado)")

    st.markdown("---")
    st.markdown("Outros tipos de upload podem ser adicionados aqui...")

if __name__ == "__main__":
    main()
