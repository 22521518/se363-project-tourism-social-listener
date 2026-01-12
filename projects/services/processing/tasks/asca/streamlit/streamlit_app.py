"""
ASCA Streamlit Monitoring App
==============================
Web interface for monitoring and managing ASCA extraction results.

Features:
- Tab 1: Dashboard - Statistics and recent extractions
- Tab 2: Review & Approve - View and approve/edit extractions
- Tab 3: Real-time Inference - Send text via chat box and see results
- Tab 4: Kafka Producer - Send single messages or batch CSV

Run:
    streamlit run streamlit_app.py --server.port 8152
"""

import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime, UTC
from pathlib import Path

# Setup path for imports
# In Docker: PYTHONPATH=/opt/airflow is set
# Locally: need to calculate project root
pythonpath = os.getenv("PYTHONPATH", "")
if pythonpath and pythonpath not in sys.path:
    sys.path.insert(0, pythonpath)
else:
    # Local development - calculate project root
    try:
        project_root = Path(__file__).resolve().parents[6]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
    except IndexError:
        # Already in correct location or different structure
        pass

from dotenv import load_dotenv
load_dotenv()  # Load from current dir or parent

import streamlit as st
import pandas as pd

# ============================================
# Configuration - Database and Kafka
# ============================================

# Hardcoded fallback config (override with .env)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "airflow"),
    "password": os.getenv("DB_PASSWORD", "airflow"),
    "database": os.getenv("DB_NAME", "airflow"),
}

KAFKA_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    "input_topic": os.getenv("KAFKA_TOPIC_ASCA_INPUT", "asca-input"),
    "output_topic": os.getenv("KAFKA_TOPIC_ASCA_OUTPUT", "asca-output"),
}

# Categories and sentiments for editing
CATEGORIES = ["LOCATION", "PRICE", "ACCOMMODATION", "FOOD", "SERVICE", "AMBIENCE"]
SENTIMENTS = ["positive", "negative", "neutral"]

# ============================================
# Database Connection with fallback
# ============================================

def get_db_connection_string():
    """Build database connection string."""
    return f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"


@st.cache_resource
def get_engine():
    """Get SQLAlchemy engine."""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(get_db_connection_string())
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


@st.cache_resource
def get_dao():
    """Get ASCA DAO instance."""
    try:
        from projects.services.processing.tasks.asca.config.settings import DatabaseConfig
        from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
        
        config = DatabaseConfig(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        return ASCAExtractionDAO(config)
    except Exception as e:
        st.error(f"Failed to initialize DAO: {e}")
        return None


def get_kafka_producer():
    """Get Kafka producer instance."""
    try:
        from projects.services.processing.tasks.asca.messaging.producer import ASCAKafkaProducer
        return ASCAKafkaProducer(
            bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
            topic=KAFKA_CONFIG['input_topic']
        )
    except Exception as e:
        st.warning(f"Kafka producer unavailable: {e}")
        return None


# ============================================
# Page Configuration
# ============================================

st.set_page_config(
    page_title="ASCA Monitoring",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 ASCA Monitoring Dashboard")
st.markdown("Aspect Category Sentiment Analysis - Monitoring & Management")

# ============================================
# Sidebar - Database Info
# ============================================

with st.sidebar:
    st.subheader("📊 Database Connection")
    st.info(f"""
**Host:** {DB_CONFIG['host']}:{DB_CONFIG['port']}  
**Database:** {DB_CONFIG['database']}
    """)
    
    st.subheader("🔗 Kafka Connection")
    st.info(f"""
**Servers:** {KAFKA_CONFIG['bootstrap_servers']}  
**Input Topic:** {KAFKA_CONFIG['input_topic']}
    """)
    
    if st.button("🔄 Clear Cache"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.success("Cache cleared!")

# ============================================
# Tabs
# ============================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Dashboard",
    "✅ Review & Approve",
    "⚡ Real-time Inference",
    "📤 Kafka Producer"
])

# ============================================
# Tab 1: Dashboard
# ============================================

with tab1:
    st.subheader("📊 Statistics")
    
    dao = get_dao()
    
    if dao:
        try:
            stats = dao.get_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Processed", stats.get('total_processed', 0))
            with col2:
                st.metric("Approved", stats.get('approved_count', 0))
            with col3:
                st.metric("Pending", stats.get('pending_count', 0))
            with col4:
                total = stats.get('total_processed', 1)
                approved = stats.get('approved_count', 0)
                rate = (approved / total * 100) if total > 0 else 0
                st.metric("Approval Rate", f"{rate:.1f}%")
            
            # Recent extractions
            st.subheader("📝 Recent Extractions")
            
            recent = dao.get_all(limit=20)
            
            if recent:
                data = []
                for r in recent:
                    aspects_str = ", ".join([
                        f"{a.category}:{a.sentiment}" 
                        for a in r.extraction_result.aspects
                    ]) or "No aspects"
                    
                    data.append({
                        "ID": r.id[:8] if r.id else "N/A",
                        "Source": r.source_type,
                        "Text": r.raw_text[:80] + "..." if len(r.raw_text) > 80 else r.raw_text,
                        "Aspects": aspects_str,
                        "Approved": "✅" if r.is_approved else "⏳"
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No extractions found.")
                
        except Exception as e:
            st.error(f"Error loading dashboard: {e}")
    else:
        st.warning("Database not connected")

# ============================================
# Tab 2: Review & Approve
# ============================================

with tab2:
    st.subheader("✅ Review & Approve Extractions")
    
    dao = get_dao()
    
    if dao:
        pending = dao.get_pending(limit=50)
        
        if pending:
            st.info(f"Found {len(pending)} pending records")
            
            for i, record in enumerate(pending[:10]):  # Show first 10
                with st.expander(f"📄 {record.source_id} - {record.raw_text[:50]}..."):
                    st.text_area("Raw Text", record.raw_text, height=100, key=f"text_{i}")
                    
                    st.write("**Extracted Aspects:**")
                    aspects = record.extraction_result.aspects
                    
                    # Editable aspects
                    edited_aspects = []
                    for j, aspect in enumerate(aspects):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            cat = st.selectbox(
                                "Category",
                                CATEGORIES,
                                index=CATEGORIES.index(aspect.category) if aspect.category in CATEGORIES else 0,
                                key=f"cat_{i}_{j}"
                            )
                        with col2:
                            sent = st.selectbox(
                                "Sentiment",
                                SENTIMENTS,
                                index=SENTIMENTS.index(aspect.sentiment) if aspect.sentiment in SENTIMENTS else 0,
                                key=f"sent_{i}_{j}"
                            )
                        with col3:
                            keep = st.checkbox("Keep", value=True, key=f"keep_{i}_{j}")
                        
                        if keep:
                            edited_aspects.append({"category": cat, "sentiment": sent, "confidence": 1.0})
                    
                    # Add new aspect
                    st.write("**Add New Aspect:**")
                    new_col1, new_col2, new_col3 = st.columns([2, 2, 1])
                    with new_col1:
                        new_cat = st.selectbox("New Category", CATEGORIES, key=f"new_cat_{i}")
                    with new_col2:
                        new_sent = st.selectbox("New Sentiment", SENTIMENTS, key=f"new_sent_{i}")
                    with new_col3:
                        if st.button("➕ Add", key=f"add_{i}"):
                            edited_aspects.append({"category": new_cat, "sentiment": new_sent, "confidence": 1.0})
                            st.rerun()
                    
                    # Action buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✅ Approve", key=f"approve_{i}"):
                            approved_result = {"aspects": edited_aspects}
                            success = dao.approve(record.id, approved_result, "streamlit_user")
                            if success:
                                st.success("Approved!")
                                st.rerun()
                            else:
                                st.error("Failed to approve")
                    with btn_col2:
                        if st.button("🗑️ Delete", key=f"delete_{i}"):
                            success = dao.soft_delete(record.id)
                            if success:
                                st.warning("Deleted")
                                st.rerun()
                            else:
                                st.error("Failed to delete")
        else:
            st.success("No pending records! All caught up. 🎉")
    else:
        st.warning("Database not connected")

# ============================================
# Tab 3: Real-time Inference
# ============================================

with tab3:
    st.subheader("⚡ Real-time Inference")
    st.markdown("Enter text to send via Kafka for ASCA processing")
    
    # Chat-like interface
    if "inference_history" not in st.session_state:
        st.session_state.inference_history = []
    
    # Input
    user_input = st.text_area(
        "Enter text for analysis:",
        placeholder="Phòng sạch sẽ, nhân viên thân thiện nhưng giá hơi cao...",
        height=100
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("🚀 Send", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)
    
    if clear_button:
        st.session_state.inference_history = []
        st.rerun()
    
    if send_button and user_input.strip():
        producer = get_kafka_producer()
        
        if producer and producer.is_available:
            result = producer.send_text(
                text=user_input.strip(),
                source_type="realtime_inference"
            )
            
            if result:
                st.session_state.inference_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "text": user_input.strip(),
                    "source_id": result.get('source_id', 'unknown'),
                    "status": "sent"
                })
                st.success(f"✅ Sent! ID: {result.get('source_id')}")
            else:
                st.error("Failed to send message")
        else:
            st.warning("Kafka producer not available. Message not sent.")
            # Still add to history for demo
            st.session_state.inference_history.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "text": user_input.strip(),
                "source_id": f"demo_{uuid.uuid4().hex[:8]}",
                "status": "demo (Kafka unavailable)"
            })
    
    # Display history
    if st.session_state.inference_history:
        st.subheader("📜 History")
        for item in reversed(st.session_state.inference_history[-10:]):
            with st.container():
                st.markdown(f"""
**{item['timestamp']}** - `{item['source_id']}` ({item['status']})  
> {item['text'][:200]}...
                """)
                st.divider()

# ============================================
# Tab 4: Kafka Producer
# ============================================

with tab4:
    st.subheader("📤 Kafka Producer")
    
    # Single message
    st.markdown("### 💬 Single Message")
    single_text = st.text_input("Enter text to send:")
    single_source_type = st.selectbox("Source Type:", ["youtube_comment", "facebook_post", "review", "other"])
    
    if st.button("📤 Send Single Message"):
        if single_text.strip():
            producer = get_kafka_producer()
            if producer and producer.is_available:
                result = producer.send_text(
                    text=single_text.strip(),
                    source_type=single_source_type
                )
                if result:
                    st.success(f"Sent! ID: {result.get('source_id')}")
                else:
                    st.error("Failed to send")
            else:
                st.warning("Kafka not available")
        else:
            st.warning("Please enter text")
    
    st.divider()
    
    # Batch upload
    st.markdown("### 📁 Batch Upload (CSV)")
    st.markdown("CSV should have a `text` column (optional: `source_type`)")
    
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df.head())
            
            if 'text' in df.columns:
                if st.button("📤 Send Batch"):
                    producer = get_kafka_producer()
                    if producer and producer.is_available:
                        texts = df['text'].dropna().tolist()
                        source_type = df.get('source_type', pd.Series(['batch'])).iloc[0] if 'source_type' in df.columns else 'batch'
                        
                        result = producer.send_batch(texts, source_type=source_type)
                        st.success(f"Sent: {result['success']} success, {result['failed']} failed")
                    else:
                        st.warning("Kafka not available")
            else:
                st.error("CSV must have a 'text' column")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    
    st.divider()
    
    # Connection diagnostics
    st.markdown("### 🔧 Connection Diagnostics")
    if st.button("Test Kafka Connection"):
        producer = get_kafka_producer()
        if producer:
            if producer.is_available:
                st.success("✅ Kafka connection OK")
            else:
                st.error("❌ Kafka producer not available")
        else:
            st.error("❌ Failed to create producer")
    
    if st.button("Test Database Connection"):
        engine = get_engine()
        if engine:
            try:
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                st.success("✅ Database connection OK")
            except Exception as e:
                st.error(f"❌ Database error: {e}")
        else:
            st.error("❌ No engine")
