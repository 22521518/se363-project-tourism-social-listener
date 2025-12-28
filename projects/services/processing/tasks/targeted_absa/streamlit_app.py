import streamlit as st
import pandas as pd
from dao import AbsaDAO
import plotly.express as px

DB_CONN = 'postgresql+psycopg2://airflow:airflow@postgres:5432/airflow'
dao = AbsaDAO(DB_CONN)

st.set_page_config(layout='wide', page_title='Targeted ABSA Monitor')
st.title('?? Targeted ABSA - Qwen 2.5 AI Monitor')

if st.sidebar.button('Refresh Data'):
    st.rerun()

try:
    data = dao.get_all_results()
except Exception as e:
    st.error(f'Database Error: {e}')
    data = []

if data:
    df = pd.DataFrame([{
        'ID': i.id, 
        'Comment': i.source_text, 
        'Aspect': i.aspect, 
        'Sentiment': i.sentiment, 
        'Correction': i.correction,
        'Time': i.processed_at
    } for i in data])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Aspect Breakdown')
        fig1 = px.pie(df, names='Aspect', hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.subheader('Sentiment Breakdown')
        fig2 = px.bar(df, x='Sentiment', color='Sentiment', barmode='group')
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader('Live Data Feed')
        st.dataframe(df, use_container_width=True, height=500)
        
    with col_right:
        st.subheader('?? Validate & Correct')
        with st.form('correction_form'):
            sid = st.number_input('ID to Correct:', min_value=0)
            new_s = st.selectbox('Correct Sentiment:', ['Positive', 'Negative', 'Neutral'])
            if st.form_submit_button('Save Correction'):
                if dao.update_correction(sid, new_s):
                    st.success(f'Updated ID {sid}!')
                    st.rerun()
                else:
                    st.error('ID not found.')
else:
    st.info('Waiting for data... Please ensure Producer is running and Spark is active.')
