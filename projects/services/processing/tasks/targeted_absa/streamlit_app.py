import streamlit as st
import pandas as pd
from dao import AbsaDAO
import plotly.express as px

# Kết nối DB
DB_CONN = f"postgresql+psycopg2://airflow:airflow@postgres:5432/airflow"
dao = AbsaDAO(DB_CONN)

st.set_page_config(layout="wide", page_title="ABSA Monitor")
st.title("?? Targeted ABSA - Qwen 2.5 Monitor")

# Sidebar
st.sidebar.header("Control Panel")
if st.sidebar.button("Làm mới dữ liệu"):
    st.rerun()

# 1. Load dữ liệu từ DB
data = dao.get_all_results()

if data:
    # Convert sang DataFrame
    df = pd.DataFrame([{
        "ID": i.id, 
        "Comment": i.source_text, 
        "Aspect": i.aspect, 
        "Sentiment": i.sentiment, 
        "Correction": i.correction,
        "Time": i.processed_at
    } for i in data])

    # 2. Thống kê
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.subheader("Phân bố Aspect")
        fig1 = px.pie(df, names='Aspect', title='Tỷ lệ các khía cạnh')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_stat2:
        st.subheader("Phân bố Cảm xúc")
        fig2 = px.bar(df, x='Sentiment', color='Sentiment', title='Số lượng theo cảm xúc')
        st.plotly_chart(fig2, use_container_width=True)

    # 3. Bảng dữ liệu & Sửa sai
    st.divider()
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Dữ liệu chi tiết")
        st.dataframe(df, use_container_width=True, height=400)

    with col2:
        st.subheader("????? Human Correction")
        with st.form("correction_form"):
            selected_id = st.number_input("Nhập ID cần sửa:", min_value=0, step=1)
            new_sentiment = st.selectbox("Chọn cảm xúc đúng:", ["Positive", "Negative", "Neutral"])
            submit = st.form_submit_button("Lưu sửa đổi")
            
            if submit:
                if dao.update_correction(selected_id, new_sentiment):
                    st.success(f"Đã sửa ID {selected_id} thành {new_sentiment}")
                    st.rerun()
                else:
                    st.error("Không tìm thấy ID này!")
else:
    st.info("Đang chờ dữ liệu từ Kafka... (Hãy chắc chắn bạn đã chạy Producer)")