import pandas as pd
import plotly.express as px
import streamlit as st

def analisar_dispositivo(df, dispositivo):
    """Análise detalhada de um dispositivo específico"""
    
    df_dispositivo = df[df['POINT_NAME'] == dispositivo].copy()
    
    df_dispositivo['DATA_COMPLETA'] = pd.to_datetime(df_dispositivo['DATE_OBJ'])
    
    df_dispositivo['DATA_HORA'] = df_dispositivo['DATA_COMPLETA'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.subheader('Estatísticas do Dispositivo')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Registros", len(df_dispositivo))
    with col2:
        dias_com_registro = df_dispositivo['DATA_COMPLETA'].dt.date.nunique()
        st.metric("Dias com Registro", dias_com_registro)
    with col3:
        status_mais_comum = df_dispositivo['STATUS'].value_counts().idxmax() if not df_dispositivo.empty else "N/A"
        st.metric("Status Mais Comum", status_mais_comum)
    
    st.subheader('Evolução Temporal dos Registros')
    
    df_por_data = df_dispositivo.groupby(df_dispositivo['DATA_COMPLETA'].dt.date).size().reset_index()
    df_por_data.columns = ['Data', 'Contagem']
    
    fig_timeline = px.line(df_por_data, x='Data', y='Contagem',
                        title=f'Quantidade de Registros por Dia - {dispositivo}',
                        markers=True)
    fig_timeline.update_layout(xaxis_title='Data', yaxis_title='Número de Registros')
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.subheader('Distribuição por Status')
    status_dispositivo = df_dispositivo['STATUS'].value_counts().reset_index()
    status_dispositivo.columns = ['Status', 'Contagem']
    
    fig_status_disp = px.pie(status_dispositivo, values='Contagem', names='Status',
                          title=f'Distribuição de Status - {dispositivo}')
    st.plotly_chart(fig_status_disp, use_container_width=True)
    
    # Gráfico de heatmap - distribuição de registros por hora do dia e dia da semana
    st.subheader('Padrões de Horário')
    
    # Extrair hora e dia da semana
    df_dispositivo['Hora'] = df_dispositivo['DATA_COMPLETA'].dt.hour
    df_dispositivo['Dia_Semana'] = df_dispositivo['DATA_COMPLETA'].dt.day_name()
    
    # Ordem dos dias da semana
    dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    heatmap_data = df_dispositivo.groupby(['Dia_Semana', 'Hora']).size().reset_index()
    heatmap_data.columns = ['Dia_Semana', 'Hora', 'Contagem']
    
    if not heatmap_data.empty and len(heatmap_data) > 1:
        # Criar um pivot table para o heatmap
        heatmap_pivot = heatmap_data.pivot(index='Dia_Semana', columns='Hora', values='Contagem')
        
        dias_presentes = [dia for dia in dias_ordem if dia in heatmap_pivot.index]
        heatmap_pivot = heatmap_pivot.loc[dias_presentes]
        
        fig_heatmap = px.imshow(heatmap_pivot,
                             labels=dict(x="Hora do Dia", y="Dia da Semana", color="Número de Registros"),
                             title=f'Distribuição de Registros por Hora e Dia - {dispositivo}',
                             color_continuous_scale='YlOrRd')
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Dados insuficientes para gerar o mapa de calor de horários.")
    
    # Tabela com histórico completo do dispositivo
    st.subheader('Histórico Completo do Dispositivo')
    st.dataframe(df_dispositivo.drop(columns=['DATE_OBJ', 'DATA_COMPLETA', 'Hora', 'Dia_Semana']), use_container_width=True)
    
    return df_dispositivo 
