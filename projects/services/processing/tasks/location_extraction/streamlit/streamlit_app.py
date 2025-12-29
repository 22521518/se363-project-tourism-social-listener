

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
    from projects.services.processing.tasks.location_extraction.dto.location_result import LocationExtractionResult, ExtractionMeta
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
    if not BACKEND_AVAILABLE:
        return
    try:
        db_config = DatabaseConfig.from_env()
        engine = create_engine(db_config.connection_string)
        Base.metadata.create_all(engine)
    except Exception as e:
        st.warning(f"⚠️ Could not initialize database tables: {e}")

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
        return dao.get_stats(
            start_date=datetime.now(UTC) - timedelta(days=30),
            end_date=datetime.now(UTC)
        )
    except Exception as e:
        st.warning(f"⚠️ Could not load statistics: {e}")
        return None

@st.cache_data(ttl=10)
def load_extractions(limit: int = 100, filter_type: str = "all", source_type: str = "All"):
    dao = get_dao()
    if not dao:
        return pd.DataFrame()
    try:
        if filter_type == "pending":
            dtos = dao.get_pending(limit=limit)
        elif filter_type == "approved":
            dtos = dao.get_approved(limit=limit)
        else:
            dtos = dao.get_all(limit=limit)
        
        if not dtos:
            return pd.DataFrame()
        
        data = []
        for dto in dtos:
            # Filter by source_type if not "All"
            if source_type != "All" and dto.source_type != source_type:
                continue
                
            extraction = dto.extraction_result
            primary = extraction.primary_location.get('name', 'N/A') if isinstance(extraction.primary_location, dict) else (extraction.primary_location.name if extraction.primary_location else "N/A")
            loc_count = len(extraction.locations) if extraction.locations else 0
            
            data.append({
                'id': dto.id,
                'source_id': dto.source_id,
                'source_type': dto.source_type,
                'raw_text': dto.raw_text,
                'primary_location': primary,
                'location_count': loc_count,
                'overall_score': extraction.overall_score,
                'is_approved': dto.is_approved,
                'extraction_result': extraction.model_dump(),
                'approved_result': dto.approved_result
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
    Get the effective extraction result.
    If approved and approved_result exists, use it. Otherwise use extraction_result.
    Returns (effective_dict, is_approved_data: bool)
    """
    if row['is_approved'] and row.get('approved_result'):
        return row['approved_result'], True
    return row['extraction_result'], False

def render_dashboard_tab():
    st.header("📊 Dashboard")
    
    stats = load_statistics()
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Processed", f"{stats.get('total_processed', 0):,}")
        with c2:
            st.metric("✅ Approved", f"{stats.get('approved_count', 0):,}")
        with c3:
            st.metric("⏳ Pending", f"{stats.get('pending_count', 0):,}")
        with c4:
            approval_rate = 0
            if stats.get('total_processed', 0) > 0:
                approval_rate = (stats.get('approved_count', 0) / stats.get('total_processed', 0)) * 100
            st.metric("📈 Approval Rate", f"{approval_rate:.1f}%")
    
    st.divider()
    
    limit = st.slider("Records to display", 10, 500, 100, 10, key="dash_limit")
    df = load_extractions(limit=limit, filter_type="all")
    
    if df.empty:
        st.info("📭 No extractions found.")
        return
    
    # Build display dataframe using effective results
    display_data = []
    for idx, row in df.iterrows():
        effective_result, is_approved_data = get_effective_extraction(row)
        
        # Get primary location from effective result
        if effective_result:
            if isinstance(effective_result, dict):
                primary = effective_result.get('primary_location', {})
                primary_name = primary.get('name', 'N/A') if isinstance(primary, dict) else 'N/A'
                loc_count = len(effective_result.get('locations', []))
                score = effective_result.get('overall_score', 0)
            else:
                primary_name = 'N/A'
                loc_count = 0
                score = 0
        else:
            primary_name = row.get('primary_location', 'N/A')
            loc_count = row.get('location_count', 0)
            score = row.get('overall_score', 0)
        
        # Status and data source indicator
        if row['is_approved']:
            status = "✅ Approved"
            data_source = "🔵" if is_approved_data else "⚪"  # Blue if using approved data
        else:
            status = "⏳ Pending"
            data_source = "⚪"
        
        display_data.append({
            'raw_text': row['raw_text'][:80] + '...' if len(row['raw_text']) > 80 else row['raw_text'],
            'primary_location': primary_name,
            'location_count': loc_count,
            'overall_score': score,
            'status': status,
            'data': data_source
        })
    
    display_df = pd.DataFrame(display_data)
    
    st.dataframe(
        display_df,
        column_config={
            'raw_text': st.column_config.TextColumn('Text', width='large'),
            'primary_location': 'Primary Location',
            'location_count': 'Locs',
            'overall_score': st.column_config.NumberColumn("Score", format="%.2f"),
            'status': 'Status',
            'data': st.column_config.TextColumn("Data", help="🔵 = Using approved data, ⚪ = Using original data")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Legend
    st.caption("🔵 = Using approved result | ⚪ = Using original extraction")
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ========================
# TAB 2: Review & Approve
# ========================
def render_review_tab():
    st.header("✅ Review & Approve")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        source_filter = st.selectbox("Filter by Source Type", ["All", "youtube_comment", "message", "telegram", "unknown"], index=0, key="review_source_filter")
    with col2:
        status_filter = st.selectbox("Status", ["pending", "approved", "all"], index=0, key="review_status_filter")
    with col3:
        if st.button("🔄 Refresh", key="review_refresh", use_container_width=True):
            clear_caches()
            st.rerun()
    
    df = load_extractions(limit=100, filter_type=status_filter, source_type=source_filter)
    
    if df.empty:
        st.success(f"🎉 No {status_filter} records found for source: {source_filter}")
        return
    
    st.info(f"📋 {len(df)} {status_filter} record(s) matching filters")
    
    # Location type options
    LOCATION_TYPES = ["city", "district", "province", "country", "region", "attraction", "address", "unknown"]
    
    for idx, row in df.iterrows():
        record_id = row['id']
        state_key = f"edit_state_{record_id}"
        expander_key = f"expander_open_{record_id}"
        
        # Initialize expander state (default to False)
        if expander_key not in st.session_state:
            st.session_state[expander_key] = False
        
        # Initialize session state for this record if not exists
        if state_key not in st.session_state or st.session_state[state_key] is None:
            # Prefer already approved result if it exists
            base_extraction = row['approved_result'] if row['is_approved'] and row['approved_result'] else row['extraction_result']
            
            # Defensive check for base_extraction
            if base_extraction is None:
                st.warning(f"⚠️ No extraction result found for record {record_id}")
                continue

            # Deep copy to avoid mutating the original until approved
            # Add a unique ID to each location to maintain widget state correctly
            loc_list = []
            try:
                # Handle both dict and object (pydantic)
                locations = base_extraction.get('locations', []) if isinstance(base_extraction, dict) else (base_extraction.locations if hasattr(base_extraction, 'locations') else [])
                
                for i, loc in enumerate(locations):
                    l = loc.copy() if hasattr(loc, 'copy') else dict(loc)
                    l['_row_id'] = f"{record_id}_loc_{i}"
                    loc_list.append(l)
                    
                primary = base_extraction.get('primary_location', {}) if isinstance(base_extraction, dict) else (base_extraction.primary_location.model_dump() if hasattr(base_extraction, 'primary_location') and base_extraction.primary_location else {})
                meta = base_extraction.get('meta', {}) if isinstance(base_extraction, dict) else (base_extraction.meta.model_dump() if hasattr(base_extraction, 'meta') else {})
                score = base_extraction.get('overall_score', 0.0) if isinstance(base_extraction, dict) else (base_extraction.overall_score if hasattr(base_extraction, 'overall_score') else 0.0)

                st.session_state[state_key] = {
                    "locations": loc_list,
                    "primary_location": primary if primary else {},
                    "overall_score": float(score),
                    "meta": meta
                }
            except Exception as e:
                st.error(f"Error initializing state for {record_id}: {e}")
                continue
        
        edit_data = st.session_state.get(state_key)
        if not edit_data:
            continue
        
        with st.expander(f"📝 {row['source_id']} - {row['raw_text'][:50]}...", expanded=st.session_state[expander_key]):
            # Update expander state on view
            st.session_state[expander_key] = True 
            st.text_area("Full Text", row['raw_text'], height=80, disabled=True, key=f"text_{record_id}")
            
            st.divider()
            st.markdown("### ✏️ Edit Extraction Result")
            
            # 📍 LOCATIONS SECTION
            st.markdown("#### 📍 Locations")
            
            # Render each location in the session state
            for loc_idx, loc in enumerate(edit_data["locations"]):
                loc_id = loc.get('_row_id', f"{record_id}_{loc_idx}")
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    
                    with c1:
                        new_name = st.text_input("Name", value=loc.get('name', ''), key=f"edit_name_{loc_id}")
                        edit_data["locations"][loc_idx]['name'] = new_name
                    
                    with c2:
                        loc_type_default = loc.get('type', 'unknown')
                        loc_type_idx = LOCATION_TYPES.index(loc_type_default) if loc_type_default in LOCATION_TYPES else len(LOCATION_TYPES) - 1
                        new_type = st.selectbox("Type", options=LOCATION_TYPES, index=loc_type_idx, key=f"edit_type_{loc_id}")
                        edit_data["locations"][loc_idx]['type'] = new_type
                    
                    with c3:
                        new_conf = st.number_input("Confidence", min_value=0.0, max_value=1.0, value=float(loc.get('confidence', 0.0)), step=0.05, key=f"edit_conf_{loc_id}")
                        edit_data["locations"][loc_idx]['confidence'] = new_conf
                    
                    with c4:
                        st.write("") # Spacer
                        if st.button("🗑️", key=f"del_loc_{loc_id}", help="Remove this location"):
                            edit_data["locations"].pop(loc_idx)
                            st.rerun()
                    
                    # Extra fields for this location
                    with st.expander(f"More fields for {loc.get('name', 'Location ' + str(loc_idx+1))}"):
                        # Display existing extra keys
                        extra_keys = [k for k in loc.keys() if k not in ["name", "type", "confidence", "_row_id"]]
                        for k in extra_keys:
                            ec1, ec2 = st.columns([1, 2])
                            with ec1:
                                st.text(f"Key: {k}")
                            with ec2:
                                edit_data["locations"][loc_idx][k] = st.text_input(f"Value for {k}", value=str(loc[k]), key=f"extra_val_{loc_id}_{k}")
                        
                        # Add new field
                        st.markdown("---")
                        nc1, nc2, nc3 = st.columns([2, 2, 1])
                        with nc1:
                            new_f_key = st.text_input("New Key", key=f"new_f_key_{loc_id}")
                        with nc2:
                            new_f_val = st.text_input("New Value", key=f"new_f_val_{loc_id}")
                        with nc3:
                            st.write("") # Spacer
                            if st.button("➕ Field", key=f"add_field_{loc_id}"):
                                if new_f_key.strip():
                                    edit_data["locations"][loc_idx][new_f_key.strip()] = new_f_val
                                    st.rerun()
                st.write("") # Space between locations
            
            if st.button("➕ Add New Location", key=f"add_loc_btn_{record_id}"):
                new_idx = len(edit_data["locations"])
                edit_data["locations"].append({
                    "name": "", 
                    "type": "unknown", 
                    "confidence": 0.0,
                    "_row_id": f"{record_id}_loc_new_{datetime.now().timestamp()}"
                })
                st.rerun()

            st.divider()
            
            # 🎯 PRIMARY LOCATION & SCORE SECTION
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🎯 Primary Location**")
                loc_names = ["(None)"] + [loc.get('name', 'Unknown') for loc in edit_data["locations"] if loc.get('name')]
                
                # Find matching index for primary location
                primary_loc = edit_data.get("primary_location")
                current_p_name = primary_loc.get('name', '(None)') if isinstance(primary_loc, dict) else '(None)'
                p_idx = 0
                if current_p_name in loc_names:
                    p_idx = loc_names.index(current_p_name)
                
                selected_primary = st.selectbox("Select Primary", options=loc_names, index=p_idx, key=f"primary_sel_{record_id}")
                
                if selected_primary == "(None)":
                    edit_data["primary_location"] = None
                else:
                    # Update primary_location object from the corresponding location in the list
                    for loc in edit_data["locations"]:
                        if loc.get('name') == selected_primary:
                            edit_data["primary_location"] = loc.copy()
                            break
            
            with c2:
                st.markdown("**📊 Overall Score**")
                edit_data["overall_score"] = st.number_input("Overall Score", min_value=0.0, max_value=1.0, value=edit_data["overall_score"], step=0.05, key=f"score_input_{record_id}")

            st.divider()
            
            # APPROVAL ACTIONS
            approver = st.text_input("Approver", value="human", key=f"approver_name_{record_id}")
            
            ac1, ac2 = st.columns(2)
            with ac1:
                btn_label = "✅ Update Approval" if row['is_approved'] else "✅ Approve"
                if st.button(btn_label, key=f"approve_btn_{record_id}", use_container_width=True, type="primary"):
                    # Prepare final result for saving
                    final_locs = []
                    for loc in edit_data["locations"]:
                        l = loc.copy()
                        if "_row_id" in l:
                            del l["_row_id"]
                        final_locs.append(l)
                    
                    final_primary = edit_data["primary_location"].copy() if edit_data["primary_location"] else None
                    if final_primary and "_row_id" in final_primary:
                        del final_primary["_row_id"]
                    
                    save_data = {
                        "locations": final_locs,
                        "primary_location": final_primary,
                        "overall_score": edit_data["overall_score"],
                        "meta": edit_data["meta"]
                    }
                    
                    dao = get_dao()
                    if dao.approve(record_id, save_data, approver):
                        st.success("Success!")
                        # Clear edit state for this record upon success
                        del st.session_state[state_key]
                        clear_caches()
                        st.rerun()
                    else:
                        st.error("Failed to save.")
            
            with ac2:
                if st.button("🗑️ Delete Record", key=f"del_rec_btn_{record_id}", use_container_width=True, type="secondary"):
                    dao = get_dao()
                    if dao.soft_delete(record_id):
                        st.success("Deleted!")
                        if state_key in st.session_state:
                            del st.session_state[state_key]
                        clear_caches()
                        st.rerun()
                    else:
                        st.error("Failed to delete.")

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
