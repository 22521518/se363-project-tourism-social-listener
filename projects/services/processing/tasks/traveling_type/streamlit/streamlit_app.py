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
    page_title="Traveling Type Monitor",
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
    from projects.services.processing.tasks.traveling_type.config import DatabaseConfig
    from projects.services.processing.tasks.traveling_type.dao import TravelingTypeDAO
    from projects.services.processing.tasks.traveling_type.models import Base,TravelingType
    from projects.services.processing.tasks.traveling_type.dto import (
        TravelingTypeDTO
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
        dao = TravelingTypeDAO(db_config)
        return dao
    except Exception as e:
        st.error(f"❌ Failed to initialize backend: {e}")
        return None

# ------------------------
# Data Loading Functions
# ------------------------
@st.cache_data(ttl=10)
def load_traveling_type_statistics():
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
def load_recent_traveling_types(limit: int = 100):
    """Load recent intentions."""
    dao = get_dao()
    if not dao:
        return pd.DataFrame()
    
    try:
        intentions = dao.get_all_traveling_types(limit=limit)
        
        if not intentions:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for intention in intentions:
            data.append({
                'id': intention.id,
                'source_id': intention.source_id,
                'raw_text': intention.raw_text,
                'traveling_type': intention.traveling_type.value,
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Could not load traveling types: {e}")
        return pd.DataFrame()

# ------------------------
# Update Form Handler
# ------------------------
def show_update_form(traveling_type_row):
    """Show modal form to update intention."""
    st.subheader("✏️ Update Traveling Type")
    
    with st.form(key=f"update_form_{traveling_type_row['id']}"):
        st.text_area("Comment Text", value=traveling_type_row['raw_text'], disabled=True, height=100)
        
   
        # Intention type selector
        traveling_types = [t.value for t in TravelingType]
        current_traveling_type_idx = traveling_types.index(traveling_type_row['traveling_type'])
            
        new_traveling_type = st.selectbox(
            "Traveling Type",
            options=traveling_types,
            index=current_traveling_type_idx,
            key=f"traveling_type_{traveling_type_row['id']}"
        )
        
        
        col_submit, col_cancel = st.columns([1, 1])
        
        with col_submit:
            submit = st.form_submit_button("💾 Save Changes", use_container_width=True)
        
        with col_cancel:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submit:
            handle_update_traveling_type(
                traveling_type_id=traveling_type_row['id'],
                source_id=traveling_type_row['source_id'],
                raw_text=traveling_type_row['raw_text'],
                new_traveling_type=new_traveling_type,
            )
            st.success("✅ Traveling type updated successfully!")
            st.rerun()
        
        if cancel:
            st.session_state.pop('editing_traveling_type', None)
            st.rerun()

def handle_update_traveling_type(traveling_type_id, source_id, raw_text, new_traveling_type):
    """Handle intention update."""
    dao = get_dao()
    if not dao:
        st.error("❌ Backend not available")
        return
    
    try:
        # Create updated DTO
        updated_dto = TravelingTypeDTO(
            id=traveling_type_id,
            source_id=source_id,
            source_type="youtube_comment",
            raw_text=raw_text,
            traveling_type=TravelingType(new_traveling_type),
        )
        
        # Update in database
        result = dao.update(updated_dto)
        
        if result:
            # Clear cache to refresh data
            load_traveling_type_statistics.clear()
            load_recent_traveling_types.clear()
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
        most_common_traveling_type = max(
            stats.by_traveling_type.items(),
            key=lambda x: x[1],
            default=("N/A", 0),
        )
        st.metric(
            "Top Traveling Type",
            most_common_traveling_type[0].title(),
            f"{most_common_traveling_type[1]:,}"
        )

    st.divider()

    # =====================
    # Breakdown sections
    # =====================

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧠 By Traveling Type")
        for k, v in sorted(stats.by_traveling_type.items(), key=lambda x: -x[1]):
            st.write(f"**{k.title()}**: {v:,}")

    with col2:
        st.markdown("### 🧾 By Source Type")
        for k, v in sorted(stats.by_source_type.items(), key=lambda x: -x[1]):
            st.write(f"**{k.title()}**: {v:,}")
    

def render_traveling_type_distribution(stats):
    """Render intention type distribution chart."""
    if not stats.by_traveling_type:
        st.info("No traveling type data available")
        return
    
    # Convert enum keys to readable strings
    traveling_type_names = [key.value if hasattr(key, 'value') else str(key) 
                       for key in stats.by_traveling_type.keys()]
    traveling_values = list(stats.by_traveling_type.values())
    
    # Create pie chart for intention types
    fig = px.pie(
        values=traveling_values,
        names=traveling_type_names,
        title="Traveling Type Distribution",
        hole=0.3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def render_traveling_types_table(df):
    """Render intentions table with edit functionality."""
    if df.empty:
        st.info("📭 No traveling type found in the database.")
        return
    
    st.subheader("📝 Recent Traveling Types")
    
    # Format the dataframe for display
    display_df = df.copy()
    display_df['raw_text'] = display_df['raw_text'].str[:100] + '...'
    
    # Display table with column configuration
    event = st.dataframe(
        display_df[['raw_text', 'traveling_type']],
        column_config={
            'raw_text': st.column_config.TextColumn('Comment', width='large'),
            'traveling_type': st.column_config.TextColumn('Traveling Type', width='medium'),
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
    stats = load_traveling_type_statistics()
    
    if not stats:
        st.warning("⚠️ No statistics available. Make sure the database is running and contains data.")
        return
    
    # Statistics Overview
    render_statistics_overview(stats)
    
    st.divider()
    
    # Charts

    render_traveling_type_distribution(stats)
    
   
    
    st.divider()
    
    # Recent Intentions Table
    traveling_types_limit = st.slider(
        "Number of traveling type to display",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        key="traveling_types_limit"
    )
    
    df = load_recent_traveling_types(limit=traveling_types_limit)
    render_traveling_types_table(df)
    
    st.divider()
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')} | Traveling Type Monitoring Dashboard")

# ------------------------
# Main Application
# ------------------------
st.title("🎯 Traveling Type Monitoring Dashboard")
st.markdown("Real-time monitoring and management of traveling type extraction results")

if not BACKEND_AVAILABLE:
    st.error("❌ Backend services are not available. Please check the configuration.")
    st.stop()

# Initialize session state
if 'editing_traveling_type' not in st.session_state:
    st.session_state.editing_traveling_type = None

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
        load_traveling_type_statistics.clear()
        load_recent_traveling_types.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("📖 Legend")
    st.markdown("""
    **Traveling Types:**
    - 💼 Business
    - 🏖️ Leisure
    - 🏔️ Adventure
    - 🎒 Backpacking
    - 💎 Luxury
    - 💰 Budget
    - 🚶 Solo
    - 👥 Group
    - 👨‍👩‍👧‍👦 Family
    - 💑 Romantic
    - ❓ Other
    """)