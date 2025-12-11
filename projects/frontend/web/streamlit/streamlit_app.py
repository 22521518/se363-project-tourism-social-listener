# SE363 – Phát triển ứng dụng trên nền tảng dữ liệu lớn
# Khoa Công nghệ Phần mềm – Trường Đại học Công nghệ Thông tin, ĐHQG-HCM
# HopDT – Faculty of Software Engineering, University of Information Technology (FSE-UIT)

# streamlit_app.py
# ======================================
# Dashboard hiển thị kết quả phân tích cảm xúc (ABSA) từ PostgreSQL
# và tự động cập nhật theo thời gian thực.

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time
import plotly.express as px

# ------------------------
# Biến toàn cục
# ------------------------

TABLE_NAME = "absa_results"

# ------------------------
# Cấu hình kết nối PostgreSQL
# ------------------------
DB_CONFIG = {
    "user": "airflow",
    "password": "airflow",
    "host": "postgres",  # dùng tên service Docker
    "port": 5432,
    "database": "airflow"
}

# ------------------------
# Hàm load dữ liệu an toàn (dùng raw_connection)
# ------------------------
@st.cache_data(ttl=5)
def load_data():
    engine = create_engine(
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    try:
        conn = engine.raw_connection()  # Lấy psycopg2 connection thực
        try:
            df = pd.read_sql(f"SELECT * FROM {TABLE_NAME} ORDER BY RANDOM() LIMIT 300", conn)
        finally:
            conn.close()  # đảm bảo đóng kết nối
        return df
    except Exception as e:
        st.warning(f"⚠️ Không thể kết nối đến PostgreSQL: {e}")
        return pd.DataFrame()

# ------------------------
# Giao diện chính
# ------------------------

# ========================
# ✅ Auto-refresh mỗi 5 giây
# ========================
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=5 * 1000, limit=None, key="auto_refresh")

# ------------------------
# Hiển thị dữ liệu
# ------------------------
df = load_data()

if df.empty:
    st.warning(f"⏳ Chưa có dữ liệu trong bảng `{TABLE_NAME}`. Hãy đảm bảo producer và consumer đang chạy.")
else:
    st.subheader("📝 Dữ liệu gần đây")
    st.dataframe(df.tail(10), use_container_width=True)
