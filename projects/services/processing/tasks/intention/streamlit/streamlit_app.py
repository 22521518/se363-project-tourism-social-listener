import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ------------------------
# Page Configuration
# ------------------------
st.set_page_config(
    page_title="Intention Monitor",
    page_icon="🎯",
    layout="wide"
)

# Add the project root to python path
project_root = Path(__file__).resolve().parents[6]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import backend services
BACKEND_AVAILABLE = False
IMPORT_ERROR_MSG = None

try:
    from projects.services.processing.tasks.intention.config import DatabaseConfig
    from projects.services.processing.tasks.intention.dao import IntentionDAO
    from projects.services.processing.tasks.intention.models import Base,IntentionType
    from projects.services.processing.tasks.intention.dto import (
        IntentionDTO
    )
    BACKEND_AVAILABLE = True
except ImportError as e:
    IMPORT_ERROR_MSG = str(e)
    BACKEND_AVAILABLE = False

if IMPORT_ERROR_MSG:
    st.error(f"Import Error: {IMPORT_ERROR_MSG}")

# ------------------------
# Database Configuration
# ------------------------
DB_CONFIG = {
    "user": "airflow",
    "password": "airflow",
    "host": "postgres",  # Use 'localhost' for local development
    "port": 5432,
    "database": "airflow"
}

def get_engine():
    """Create SQLAlchemy engine."""
    return create_engine(
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )

def initialize_database():
    """Initialize database tables if they don't exist."""
    if not BACKEND_AVAILABLE:
        return
    
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
    except Exception as e:
        st.warning(f"⚠️ Could not initialize database tables: {e}")

# Run database initialization on app start
initialize_database()

# ------------------------
# Backend Initialization
# ------------------------
@st.cache_resource
def get_dao():
    """Initialize and cache the DAO."""
    try:
        if not BACKEND_AVAILABLE:
            st.error("❌ Backend services not found.")
            return None
            
        db_config = DatabaseConfig.from_env()
        dao = IntentionDAO(db_config)
        return dao
    except Exception as e:
        st.error(f"❌ Failed to initialize backend: {e}")
        return None

# ------------------------
# Data Loading Functions
# ------------------------
@st.cache_data(ttl=10)
def load_intention_statistics():
    """Load overall intention statistics."""
    dao = get_dao()
    if not dao:
        return None
    
    try:
        # Get stats for last 30 days
        stats = dao.get_stats(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        return stats
    except Exception as e:
        st.warning(f"⚠️ Could not load statistics: {e}")
        return None

@st.cache_data(ttl=10)
def load_recent_intentions(limit: int = 100):
    """Load recent intentions."""
    dao = get_dao()
    if not dao:
        return pd.DataFrame()
    
    try:
        intentions = dao.get_all_intentions(limit=limit)
        
        if not intentions:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for intention in intentions:
            data.append({
                'id': intention.id,
                'source_id': intention.source_id,
                'raw_text': intention.raw_text,
                'intention_type': intention.intention_type.value,
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Could not load intentions: {e}")
        return pd.DataFrame()

# ------------------------
# Update Form Handler
# ------------------------
def show_update_form(intention_row):
    """Show modal form to update intention."""
    st.subheader("✏️ Update Intention")
    
    with st.form(key=f"update_form_{intention_row['id']}"):
        st.text_area("Comment Text", value=intention_row['raw_text'], disabled=True, height=100)
        
   
        # Intention type selector
        intention_types = [t.value for t in IntentionType]
        current_intention_idx = intention_types.index(intention_row['intention_type'])
            
        new_intention = st.selectbox(
            "Intention Type",
            options=intention_types,
            index=current_intention_idx,
            key=f"intention_{intention_row['id']}"
        )
        
        
        col_submit, col_cancel = st.columns([1, 1])
        
        with col_submit:
            submit = st.form_submit_button("💾 Save Changes", use_container_width=True)
        
        with col_cancel:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submit:
            handle_update_intention(
                intention_id=intention_row['id'],
                source_id=intention_row['source_id'],
                raw_text=intention_row['raw_text'],
                new_intention=new_intention,
            )
            st.success("✅ Intention updated successfully!")
            st.rerun()
        
        if cancel:
            st.session_state.pop('editing_intention', None)
            st.rerun()

def handle_update_intention(intention_id, source_id, raw_text, new_intention):
    """Handle intention update."""
    dao = get_dao()
    if not dao:
        st.error("❌ Backend not available")
        return
    
    try:
        # Create updated DTO
        updated_dto = IntentionDTO(
            id=intention_id,
            source_id=source_id,
            source_type="youtube_comment",
            raw_text=raw_text,
            intention_type=IntentionType(new_intention),
        )
        
        # Update in database
        result = dao.update(updated_dto)
        
        if result:
            # Clear cache to refresh data
            load_intention_statistics.clear()
            load_recent_intentions.clear()
        else:
            st.error("❌ Failed to update intention")
            
    except Exception as e:
        st.error(f"❌ Error updating intention: {e}")

# ------------------------
# Visualization Components
# ------------------------
def render_statistics_overview(stats):
    """Render statistics overview cards."""
    if not stats:
        st.info("No statistics available.")
        return

    st.subheader("📊 Statistics Overview (Last 30 Days)")

    # =====================
    # Top-level metrics
    # =====================
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Processed",
            f"{stats.total_processed:,}"
        )

    with col2:
        most_common_intention = max(
            stats.by_intention_type.items(),
            key=lambda x: x[1],
            default=("N/A", 0),
        )
        st.metric(
            "Top Intention",
            most_common_intention[0].title(),
            f"{most_common_intention[1]:,}"
        )

    st.divider()

    # =====================
    # Breakdown sections
    # =====================

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧠 By Intention Type")
        for k, v in sorted(stats.by_intention_type.items(), key=lambda x: -x[1]):
            st.write(f"**{k.title()}**: {v:,}")

    with col2:
        st.markdown("### 🧾 By Source Type")
        for k, v in sorted(stats.by_source_type.items(), key=lambda x: -x[1]):
            st.write(f"**{k.title()}**: {v:,}")
    

def render_intention_distribution(stats):
    """Render intention type distribution chart."""
    if not stats.by_intention_type:
        st.info("No intention data available")
        return
    
    # Convert enum keys to readable strings
    intention_names = [key.value if hasattr(key, 'value') else str(key) 
                       for key in stats.by_intention_type.keys()]
    intention_values = list(stats.by_intention_type.values())
    
    # Create pie chart for intention types
    fig = px.pie(
        values=intention_values,
        names=intention_names,
        title="Intention Type Distribution",
        hole=0.3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def render_intentions_table(df):
    """Render intentions table with edit functionality."""
    if df.empty:
        st.info("📭 No intentions found in the database.")
        return
    
    st.subheader("📝 Recent Intentions")
    
    # Format the dataframe for display
    display_df = df.copy()
    display_df['raw_text'] = display_df['raw_text'].str[:100] + '...'
    
    # Display table with column configuration
    event = st.dataframe(
        display_df[['raw_text', 'intention_type']],
        column_config={
            'raw_text': st.column_config.TextColumn('Comment', width='large'),
            'intention_type': st.column_config.TextColumn('Intention', width='medium'),
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Handle row selection
    if event.selection and event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_row = df.iloc[selected_idx]
        
        st.divider()
        
        # Show update form
        show_update_form(selected_row)

# ------------------------
# Auto-refresh Dashboard
# ------------------------
@st.fragment(run_every=10)
def render_dashboard():
    """Render the main dashboard with auto-refresh."""
    
    # Load data
    stats = load_intention_statistics()
    
    if not stats:
        st.warning("⚠️ No statistics available. Make sure the database is running and contains data.")
        return
    
    # Statistics Overview
    render_statistics_overview(stats)
    
    st.divider()
    
    # Charts

    render_intention_distribution(stats)
    
   
    
    st.divider()
    
    # Recent Intentions Table
    intentions_limit = st.slider(
        "Number of intentions to display",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        key="intentions_limit"
    )
    
    df = load_recent_intentions(limit=intentions_limit)
    render_intentions_table(df)
    
    st.divider()
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')} | Intention Monitoring Dashboard")

# ------------------------
# Main Application
# ------------------------
st.title("🎯 Intention Monitoring Dashboard")
st.markdown("Real-time monitoring and management of intention extraction results")

if not BACKEND_AVAILABLE:
    st.error("❌ Backend services are not available. Please check the configuration.")
    st.stop()

# Initialize session state
if 'editing_intention' not in st.session_state:
    st.session_state.editing_intention = None

# Render the dashboard
render_dashboard()

# Sidebar with additional controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("Database Info")
    st.info(f"""
    **Host:** {DB_CONFIG['host']}  
    **Database:** {DB_CONFIG['database']}  
    **User:** {DB_CONFIG['user']}
    """)
    
    st.divider()
    
    st.subheader("🔄 Refresh Data")
    if st.button("Clear Cache & Refresh", use_container_width=True):
        load_intention_statistics.clear()
        load_recent_intentions.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("📖 Legend")
    st.markdown("""
    **Intention Types:**
    - 🤔 Question
    - 💬 Feedback
    - 😡 Complaint
    - 💡 Suggestion
    - 👏 Praise
    - 🙏 Request
    - 💭 Discussion
    - 🚫 Spam
    - ❓ Other
    """)