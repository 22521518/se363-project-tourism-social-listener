

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, UTC
import plotly.express as px
import json

# ------------------------
# Page Configuration
# ------------------------
st.set_page_config(
    page_title="Location Extraction Monitor",
    page_icon="🗺️",
    layout="wide"
)

# Add the project root to python path
project_root = Path(__file__).resolve().parents[6]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import backend services
BACKEND_AVAILABLE = False
KAFKA_AVAILABLE = False
IMPORT_ERROR_MSG = None

try:
    from projects.services.processing.tasks.location_extraction.config.settings import DatabaseConfig, KafkaConfig
    from projects.services.processing.tasks.location_extraction.dao.dao import LocationExtractionDAO
    from projects.services.processing.tasks.location_extraction.orm.models import Base
    from projects.services.processing.tasks.location_extraction.dto.persistence import PersistenceLocationDTO
    from projects.services.processing.tasks.location_extraction.dto.location_result import LocationExtractionResult, Location
    BACKEND_AVAILABLE = True
except ImportError as e:
    IMPORT_ERROR_MSG = str(e)
    BACKEND_AVAILABLE = False

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

if IMPORT_ERROR_MSG:
    st.error(f"Import Error: {IMPORT_ERROR_MSG}")

# ------------------------
# Database Initialization
# ------------------------
def initialize_database():
    """Initialize database tables if they don't exist (auto-init via DAO)."""
    if not BACKEND_AVAILABLE:
        return
    try:
        db_config = DatabaseConfig.from_env()
        # DAO auto-initializes tables when created (auto_init=True by default)
        dao = LocationExtractionDAO(db_config)
        st.session_state['_db_initialized'] = True
    except Exception as e:
        st.warning(f"⚠️ Could not initialize database tables: {e}")

# Only initialize once
if '_db_initialized' not in st.session_state:
    initialize_database()

# ------------------------
# Backend Initialization
# ------------------------
@st.cache_resource
def get_dao():
    try:
        if not BACKEND_AVAILABLE:
            return None
        db_config = DatabaseConfig.from_env()
        return LocationExtractionDAO(db_config)
    except Exception as e:
        st.error(f"❌ Failed to initialize backend: {e}")
        return None

@st.cache_resource
def get_kafka_producer():
    if not KAFKA_AVAILABLE or not BACKEND_AVAILABLE:
        return None
    try:
        kafka_config = KafkaConfig.from_env()
        producer = KafkaProducer(
            # bootstrap_servers=kafka_config.bootstrap_servers,
            bootstrap_servers="kafka:9092",
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            request_timeout_ms=10000,      # Reduced for faster failure detection
            linger_ms=10,
            batch_size=32768,
            acks=1,
            retries=2                      # Reduced for UI responsiveness
        )
        return producer
    except Exception as e:
        st.warning(f"⚠️ Kafka producer not available: {e}")
        return None

def test_kafka_connection():
    """Test connection to Kafka and return status + details."""
    if not KAFKA_AVAILABLE:
        return False, "kafka-python-ng not installed", []
    
    try:
        from kafka import KafkaConsumer
        kafka_config = KafkaConfig.from_env()
        # Use a short-lived consumer to check connectivity
        consumer = KafkaConsumer(
            bootstrap_servers=kafka_config.bootstrap_servers,
            request_timeout_ms=5000,
            connections_max_idle_ms=5000,
        )
        topics = consumer.topics()
        consumer.close()
        return True, "Connected successfully", list(topics)
    except Exception as e:
        return False, str(e), []

# ------------------------
# Data Loading Functions
# ------------------------
@st.cache_data(ttl=10)
def load_statistics():
    dao = get_dao()
    if not dao:
        return None
    try:
        return dao.get_stats()
    except Exception as e:
        st.warning(f"⚠️ Could not load statistics: {e}")
        return None

@st.cache_data(ttl=10)
def load_extractions(limit: int = 100, source_type: str = "All"):
    dao = get_dao()
    if not dao:
        return pd.DataFrame()
    try:
        # Simplified DAO only has get_all
        dtos = dao.get_all(limit=limit)
        
        if not dtos:
            return pd.DataFrame()
        
        data = []
        for dto in dtos:
            # Filter by source_type if not "All"
            if source_type != "All" and dto.source_type != source_type:
                continue
                
            extraction = dto.extraction_result
            loc_count = len(extraction.locations) if extraction.locations else 0
            # Calculate score from first location if available
            first_loc_score = extraction.locations[0].score if extraction.locations else 0.0
            
            data.append({
                'id': dto.id,
                'source_id': dto.source_id,
                'source_type': dto.source_type,
                'raw_text': dto.raw_text,
                'location_count': loc_count,
                'score': first_loc_score,
                'extraction_result': extraction.model_dump()
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Could not load extractions: {e}")
        return pd.DataFrame()

def clear_caches():
    load_statistics.clear()
    load_extractions.clear()

# ========================
# TAB 1: Dashboard
# ========================
def get_effective_extraction(row):
    """
    Get the extraction result from the row.
    Returns (extraction_dict, False) - simplified schema has no approval.
    """
    return row['extraction_result'], False

def render_dashboard_tab():
    st.header("📊 Dashboard")
    
    stats = load_statistics()
    if stats:
        st.metric("Total Processed", f"{stats.get('total_processed', 0):,}")
    
    st.divider()
    
    limit = st.slider("Records to display", 10, 500, 100, 10, key="dash_limit")
    df = load_extractions(limit=limit)
    
    if df.empty:
        st.info("📭 No extractions found.")
        return
    
    # Build display dataframe using effective results
    display_data = []
    for idx, row in df.iterrows():
        effective_result, is_approved_data = get_effective_extraction(row)
        
        # Get location info from effective result
        if effective_result:
            if isinstance(effective_result, dict):
                locations = effective_result.get('locations', [])
                loc_count = len(locations)
                # Get first location as primary
                first_loc = locations[0].get('word', 'N/A') if locations else 'N/A'
                score = locations[0].get('score', 0) if locations else 0
            else:
                loc_count = 0
                first_loc = 'N/A'
                score = 0
        else:
            loc_count = row.get('location_count', 0)
            first_loc = 'N/A'
            score = row.get('score', 0)
        
        display_data.append({
            'raw_text': row['raw_text'][:80] + '...' if len(row['raw_text']) > 80 else row['raw_text'],
            'first_location': first_loc,
            'location_count': loc_count,
            'score': score
        })
    
    display_df = pd.DataFrame(display_data)
    
    st.dataframe(
        display_df,
        column_config={
            'raw_text': st.column_config.TextColumn('Text', width='large'),
            'first_location': 'First Location',
            'location_count': 'Locs',
            'score': st.column_config.NumberColumn("Score", format="%.2f")
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ========================
# TAB 2: Review & Approve
# ========================
def render_review_tab():
    st.header("📝 Extraction Details")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        source_filter = st.selectbox("Filter by Source Type", ["All", "youtube_comment", "message", "telegram", "unknown"], index=0, key="review_source_filter")
    with col2:
        if st.button("🔄 Refresh", key="review_refresh", use_container_width=True):
            clear_caches()
            st.rerun()
    
    df = load_extractions(limit=100, source_type=source_filter)
    
    if df.empty:
        st.info("📬 No records found for source: " + source_filter)
        return
    
    st.info(f"📋 {len(df)} record(s) matching filters")
    
    # Display each extraction record (read-only view for simplified schema)
    for idx, row in df.iterrows():
        record_id = row['id']
        extraction = row['extraction_result']
        
        with st.expander(f"📝 {row['source_id']} - {row['raw_text'][:50]}..."):
            st.text_area("Full Text", row['raw_text'], height=80, disabled=True, key=f"text_{record_id}")
            
            st.divider()
            st.markdown("### 📍 Extracted Locations")
            
            # Get locations from extraction
            locations = extraction.get('locations', []) if isinstance(extraction, dict) else []
            
            if locations:
                loc_data = []
                for loc in locations:
                    loc_data.append({
                        'Word': loc.get('word', ''),
                        'Score': f"{loc.get('score', 0):.2f}",
                        'Entity Group': loc.get('entity_group', 'LOC'),
                        'Start': loc.get('start', 0),
                        'End': loc.get('end', 0)
                    })
                st.dataframe(pd.DataFrame(loc_data), hide_index=True, use_container_width=True)
            else:
                st.info("No locations extracted")
            
            # Show raw JSON
            with st.expander("🔍 Raw Extraction Result"):
                st.json(extraction)

# ========================
# TAB 3: Kafka Producer
# ========================
def render_kafka_tab():
    st.header("📤 Kafka Producer")
    st.markdown("Send messages to trigger LLM location extraction processing.")
    
    if not KAFKA_AVAILABLE:
        st.error("❌ kafka-python-ng is not installed. Please add it to requirements.txt")
        return
    
    producer = get_kafka_producer()
    if not producer:
        st.warning("⚠️ Could not connect to Kafka. Make sure Kafka is running.")
        kafka_config = KafkaConfig.from_env() if BACKEND_AVAILABLE else None
        broker_info = kafka_config.bootstrap_servers if kafka_config else "Unknown"
        st.info(f"Kafka broker: `{broker_info}` (configured in .env)")
    
    kafka_config = KafkaConfig.from_env() if BACKEND_AVAILABLE else None
    
    st.subheader("📨 Send Single Message")
    
    with st.form("single_message_form"):
        text_content = st.text_area("Text Content", placeholder="Enter the text to extract locations from...", height=100)
        
        submit = st.form_submit_button("📤 Send to Kafka", use_container_width=True)
        
        if submit:
            if not text_content:
                st.error("Please enter text content")
            elif not producer:
                st.error("Kafka producer not available")
            else:
                # Auto-generate source_id if not provided
                import uuid
                final_source_id = f"message_{uuid.uuid4().hex[:12]}"
                
                message = {
                    "source_id": final_source_id,
                    "source_type": "message",
                    "text": text_content,
                    "timestamp": datetime.now(UTC).isoformat()
                }
                try:
                    # Record the message in history
                    if "kafka_history" not in st.session_state:
                        st.session_state["kafka_history"] = []
                    
                    st.info(f"Sending message to Kafka [{kafka_config.input_topic}]: {message}")

                    future = producer.send(
                        kafka_config.input_topic,
                        key=final_source_id,
                        value=message
                    )

                    # Wait for metadata to confirm send
                    metadata = future.get(timeout=10)
                    producer.flush()
                    
                    hist_entry = {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "source_id": final_source_id,
                        "topic": kafka_config.input_topic,
                        "partition": 0,
                        "offset": 0,
                        "status": "✅ Sent"
                    }
                    st.session_state["kafka_history"].insert(0, hist_entry)
                    st.session_state["kafka_history"] = st.session_state["kafka_history"][:10] # Keep last 10
                    
                    st.success(f"✅ Message sent successfully!")
                    st.info(f"Topic: `{kafka_config.input_topic}`, Partition: `0`, Offset: `0`")
                    st.json(message)
                except Exception as e:
                    st.error(f"Failed to send message [{kafka_config.input_topic}]: {e}")
                    if "kafka_history" not in st.session_state:
                        st.session_state["kafka_history"] = []
                    st.session_state["kafka_history"].insert(0, {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "source_id": final_source_id,
                        "status": f"❌ Error: {str(e)[:50]}..."
                    })
    
    st.divider()
    
    st.subheader("📦 Batch Upload")
    st.markdown("Upload a CSV file with columns: `source_id`, `source_type`, `text`")
    
    uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.dataframe(batch_df.head(10))
            
            if st.button("📤 Send All to Kafka"):
                if not producer:
                    st.error("Kafka producer not available")
                else:
                    success_count = 0
                    if "kafka_history" not in st.session_state:
                        st.session_state["kafka_history"] = []
                        
                    for _, row in batch_df.iterrows():
                        msg_id = str(row.get('source_id', f"batch_{uuid.uuid4().hex[:8]}"))
                        message = {
                            "source_id": msg_id,
                            "source_type": str(row.get('source_type', 'unknown')),
                            "text": str(row.get('text', '')),
                            "timestamp": datetime.now(UTC).isoformat()
                        }
                        try:
                            producer.send(kafka_config.input_topic, key=message['source_id'], value=message)
                            success_count += 1
                        except:
                            pass
                    producer.flush()
                    st.success(f"✅ Sent {success_count}/{len(batch_df)} messages")
                    
                    st.session_state["kafka_history"].insert(0, {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "source_id": f"Batch ({success_count} msgs)",
                        "status": "✅ Batch Sent"
                    })
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    
    # Sent Messages History
    if "kafka_history" in st.session_state and st.session_state["kafka_history"]:
        st.divider()
        st.subheader("📜 Sent Messages History (Recent)")
        hist_df = pd.DataFrame(st.session_state["kafka_history"])
        st.table(hist_df)
    
    st.divider()
    st.subheader("ℹ️ Kafka Configuration & Diagnostics")
    if kafka_config:
        import os
        is_docker = os.path.exists('/.dockerenv')
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Host Environment:** {'container 🐳' if is_docker else 'Host/Terminal 💻'}")
            st.markdown(f"**Bootstrap Servers:** `{kafka_config.bootstrap_servers}`")
            st.markdown(f"**Input Topic:** `{kafka_config.input_topic}`")
        with c2:
            if st.button("🔍 Test Kafka Connection", key="test_kafka_btn"):
                with st.spinner("Connecting to Kafka..."):
                    success, msg, topics = test_kafka_connection()
                    if success:
                        st.success(f"✅ {msg}")
                        st.write(f"**Available Topics:** {', '.join(topics) if topics else 'None'}")
                    else:
                        st.error(f"❌ Connection Failed: {msg}")
                        st.info("💡 If you are in Docker, ensure you use `kafka:9092`. If in Terminal, use `localhost:9092`.")
        
        with st.expander("Show detailed settings"):
            st.code(f"""
Bootstrap Servers: {kafka_config.bootstrap_servers}
Input Topic: {kafka_config.input_topic}
Output Topic: {kafka_config.output_topic}
Consumer Group: {kafka_config.consumer_group}
            """)

# ========================
# Main Application
# ========================
st.title("🗺️ Location Extraction Monitor")

if not BACKEND_AVAILABLE:
    st.error("❌ Backend services are not available. Please check the configuration.")
    st.stop()

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "✅ Review & Approve", "📤 Kafka Producer"])

with tab1:
    render_dashboard_tab()

with tab2:
    render_review_tab()

with tab3:
    render_kafka_tab()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # DB Diagnostics
    with st.expander("🛠️ Database Diagnostics"):
        try:
            db_config = DatabaseConfig.from_env()
            st.write(f"**Host:** `{db_config.host}`")
            st.write(f"**Port:** `{db_config.port}`")
            st.write(f"**Name:** `{db_config.database}`")
            st.write(f"**User:** `{db_config.user}`")
            
            dao = get_dao()
            if dao:
                with dao.get_session() as session:
                    res = session.execute(text("SELECT 1")).fetchone()
                    if res:
                        st.success("✅ Connected to DB")
        except Exception as e:
            st.error(f"❌ DB Error: {e}")

    if st.button("Clear Cache & Refresh", use_container_width=True):
        clear_caches()
        # Also clear session state edit states
        for key in list(st.session_state.keys()):
            if key.startswith("edit_state_"):
                del st.session_state[key]
        st.rerun()
    
    st.divider()
    st.markdown("**Kafka Status:**")
    if KAFKA_AVAILABLE:
        st.success("✅ kafka-python-ng installed")
    else:
        st.warning("⚠️ kafka-python-ng not installed")
