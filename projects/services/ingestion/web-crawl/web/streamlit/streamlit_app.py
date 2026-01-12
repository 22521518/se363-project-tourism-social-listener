"""
Web Crawl Monitor Dashboard - Streamlit app for monitoring web crawl operations.

Features:
- Dashboard: Statistics, recent crawls, content type distribution
- History: View and filter crawl history
- Actions: Submit crawl requests via Kafka

NOTE: This app uses SQL-only for database access.
Actions are performed through Kafka messaging.
"""
import sys
import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go

# Kafka imports
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# ------------------------
# Configuration
# ------------------------
DB_CONFIG = {
    "user": os.getenv("DB_USER", "airflow"),
    "password": os.getenv("DB_PASSWORD", "airflow"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "airflow"),
}

KAFKA_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "requests_topic": "webcrawl.requests",
}


# ------------------------
# Database Functions
# ------------------------
@st.cache_resource
def get_engine():
    """Create SQLAlchemy engine."""
    conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_str)


# ------------------------
# Database Initialization
# ------------------------
def initialize_database():
    """Initialize database tables if they don't exist."""
    try:
        # Import ORM models and init function
        # Set environment variables for ORM base before import
        import os
        os.environ.setdefault("DB_HOST", DB_CONFIG["host"])
        os.environ.setdefault("DB_PORT", str(DB_CONFIG["port"]))
        os.environ.setdefault("DB_NAME", DB_CONFIG["database"])
        os.environ.setdefault("DB_USER", DB_CONFIG["user"])
        os.environ.setdefault("DB_PASSWORD", DB_CONFIG["password"])
        
        # Now import and initialize
        from projects.services.ingestion.web_crawl.orm.base import init_db
        init_db()
        st.session_state['_db_initialized'] = True
    except ImportError as e:
        # If ORM import fails, try to create tables via raw SQL
        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Check if tables exist
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'crawl_history'
                    )
                """)).scalar()
                
                if not result:
                    # Create tables via raw SQL as fallback
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS crawl_history (
                            id SERIAL PRIMARY KEY,
                            request_id VARCHAR(36) UNIQUE NOT NULL,
                            url VARCHAR(2048) NOT NULL,
                            content_type VARCHAR(50) NOT NULL,
                            crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                            error_message VARCHAR(1024)
                        );
                        CREATE INDEX IF NOT EXISTS idx_crawl_history_request_id ON crawl_history(request_id);
                    """))
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS crawl_result (
                            id SERIAL PRIMARY KEY,
                            crawl_history_id INTEGER UNIQUE NOT NULL REFERENCES crawl_history(id) ON DELETE CASCADE,
                            title VARCHAR(512),
                            information TEXT,
                            language VARCHAR(10),
                            reviews_json JSONB DEFAULT '[]',
                            comments_json JSONB DEFAULT '[]',
                            blog_sections_json JSONB DEFAULT '[]',
                            agency_info_json JSONB,
                            detected_sections JSONB DEFAULT '[]',
                            crawl_strategy VARCHAR(20) DEFAULT 'single',
                            extraction_strategy VARCHAR(20) DEFAULT 'llm'
                        );
                    """))
                    conn.commit()
                st.session_state['_db_initialized'] = True
        except Exception as sql_e:
            st.warning(f"⚠️ Could not initialize database tables: {sql_e}")
    except Exception as e:
        st.warning(f"⚠️ Could not initialize database tables: {e}")


# Initialize database on first load
if '_db_initialized' not in st.session_state:
    initialize_database()


@st.cache_data(ttl=60)
def load_statistics():
    """Load overall statistics."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Total crawls
            total = conn.execute(text(
                "SELECT COUNT(*) FROM crawl_history"
            )).scalar() or 0
            
            # Completed crawls
            completed = conn.execute(text(
                "SELECT COUNT(*) FROM crawl_history WHERE status = 'COMPLETED'"
            )).scalar() or 0
            
            # Failed crawls
            failed = conn.execute(text(
                "SELECT COUNT(*) FROM crawl_history WHERE status = 'FAILED'"
            )).scalar() or 0
            
            # Content type distribution
            content_types = pd.read_sql(text("""
                SELECT content_type, COUNT(*) as count
                FROM crawl_history
                GROUP BY content_type
                ORDER BY count DESC
            """), conn)
            
            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": total - completed - failed,
                "content_types": content_types,
            }
    except Exception as e:
        st.error(f"Database error: {e}")
        return {"total": 0, "completed": 0, "failed": 0, "pending": 0, "content_types": pd.DataFrame()}


@st.cache_data(ttl=60)
def load_recent_crawls(limit: int = 20):
    """Load recent crawl history."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(f"""
                SELECT 
                    h.request_id,
                    h.url,
                    h.content_type,
                    h.status,
                    h.crawl_time,
                    h.error_message,
                    r.title
                FROM crawl_history h
                LEFT JOIN crawl_result r ON h.id = r.crawl_history_id
                ORDER BY h.crawl_time DESC
                LIMIT {limit}
            """), conn)
            return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_crawl_details(request_id: str):
    """Load details for a specific crawl."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = pd.read_sql(text("""
                SELECT 
                    h.request_id,
                    h.url,
                    h.content_type,
                    h.status,
                    h.crawl_time,
                    h.error_message,
                    r.title,
                    r.information,
                    r.reviews_json,
                    r.comments_json,
                    r.blog_sections_json,
                    r.detected_sections
                FROM crawl_history h
                LEFT JOIN crawl_result r ON h.id = r.crawl_history_id
                WHERE h.request_id = :request_id
            """), conn, params={"request_id": request_id})
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None


# ------------------------
# Kafka Functions
# ------------------------
def get_kafka_producer():
    """Get Kafka producer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_CONFIG["bootstrap_servers"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        return producer
    except NoBrokersAvailable:
        st.error(f"Kafka not available at {KAFKA_CONFIG['bootstrap_servers']}")
        return None


def submit_crawl_request(url: str, content_type: str, force_refresh: bool = False):
    """Submit a crawl request to Kafka."""
    producer = get_kafka_producer()
    if not producer:
        return False
    
    try:
        message = {
            "event_type": "crawl_request",
            "url": url,
            "content_type": content_type,
            "force_refresh": force_refresh,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        producer.send(
            KAFKA_CONFIG["requests_topic"],
            key=url,
            value=message,
        )
        producer.flush()
        producer.close()
        return True
    except Exception as e:
        st.error(f"Failed to submit request: {e}")
        return False


# ------------------------
# Dashboard UI
# ------------------------
@st.fragment
def render_dashboard():
    """Render the main dashboard."""
    st.header("📊 Dashboard")
    
    # Load statistics
    stats = load_statistics()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Crawls", stats["total"])
    with col2:
        st.metric("Completed", stats["completed"], delta=None)
    with col3:
        st.metric("Failed", stats["failed"], delta=None, delta_color="inverse")
    with col4:
        st.metric("Pending", stats["pending"])
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status Distribution")
        status_data = pd.DataFrame({
            "Status": ["Completed", "Failed", "Pending"],
            "Count": [stats["completed"], stats["failed"], stats["pending"]]
        })
        fig = px.pie(status_data, values="Count", names="Status", 
                     color="Status",
                     color_discrete_map={"Completed": "#2ecc71", "Failed": "#e74c3c", "Pending": "#f39c12"})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Content Type Distribution")
        if not stats["content_types"].empty:
            fig = px.bar(stats["content_types"], x="content_type", y="count",
                        color="content_type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    # Recent crawls
    st.subheader("Recent Crawls")
    recent = load_recent_crawls(10)
    if not recent.empty:
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("No crawls found")



@st.cache_data(ttl=60)
def load_filtered_history(status_filter: str, content_filter: str, limit: int):
    """Load history with filters."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            query = """
                SELECT 
                    h.request_id,
                    h.url,
                    h.content_type,
                    h.status,
                    h.crawl_time,
                    r.title
                FROM crawl_history h
                LEFT JOIN crawl_result r ON h.id = r.crawl_history_id
                WHERE 1=1
            """
            # Helper to effectively ignore 'All' filters in SQL construction
            # But since we cache based on args, passing "All" is fine, we just handle logic here
            if status_filter != "All":
                query += f" AND h.status = '{status_filter}'"
            if content_filter != "All":
                query += f" AND h.content_type = '{content_filter}'"
            
            query += f" ORDER BY h.crawl_time DESC LIMIT {limit}"
            
            return pd.read_sql(text(query), conn)
    except Exception as e:
        # We can't use st.error here easily if we want to return a clean DataFrame
        # ideally we return empty DF and let caller handle, or just return empty
        print(f"Query error: {e}") 
        return pd.DataFrame()


@st.fragment
def render_history():
    """Render the history tab."""
    st.header("📜 Crawl History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "COMPLETED", "FAILED", "PENDING", "IN_PROGRESS"])
    with col2:
        content_filter = st.selectbox("Content Type", ["All", "forum", "review", "blog", "agency", "auto"])
    with col3:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=50)
    
    # Load data with filters
    df = load_filtered_history(status_filter, content_filter, limit)
    
    if not df.empty:
        # Show as table
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Detail view
        st.subheader("View Details")
        selected_id = st.selectbox("Select Request ID", df["request_id"].tolist())
        
        if selected_id and st.button("Load Details"):
            details = load_crawl_details(selected_id)
            if details:
                st.json(details)
    else:
        st.info("No history found")


@st.fragment
def render_actions():
    """Render the actions tab."""
    st.header("🚀 Submit Crawl Request")
    
    st.info("Submit a new crawl request via Kafka. The request will be processed by the web crawl service.")
    
    with st.form("crawl_form"):
        url = st.text_input("URL to Crawl", placeholder="https://example.com/tourism-page")
        content_type = st.selectbox("Content Type", ["auto", "forum", "review", "blog", "agency"])
        force_refresh = st.checkbox("Force Re-crawl (ignore cache)")
        
        submitted = st.form_submit_button("Submit Crawl Request")
        
        if submitted:
            if not url:
                st.error("Please enter a URL")
            else:
                if submit_crawl_request(url, content_type, force_refresh):
                    st.success(f"✅ Crawl request submitted for: {url}")
                else:
                    st.error("Failed to submit request")


# ------------------------
# Main App
# ------------------------
st.set_page_config(
    page_title="Web Crawl Monitor",
    page_icon="🕷️",
    layout="wide",
)

st.title("🕷️ Web Crawl Monitor Dashboard")
st.markdown("Monitor web crawl operations and submit new crawl requests.")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📜 History", "🚀 Actions"])

with tab1:
    render_dashboard()

with tab2:
    render_history()

with tab3:
    render_actions()

# Footer
st.markdown("---")
st.caption("Web Crawl Ingestion Module | Connected to Kafka for actions")
