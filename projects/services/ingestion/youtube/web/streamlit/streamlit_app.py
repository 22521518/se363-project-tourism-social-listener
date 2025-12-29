import sys
from pathlib import Path
import asyncio
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ------------------------
# Page Configuration
# ------------------------
# Must be the first Streamlit command
st.set_page_config(
    page_title="YouTube Monitor",
    page_icon="📺",
    layout="wide"
)

# Add the project root to python path to allow absolute imports of the framework
# File location: projects/services/ingestion/youtube/web/streamlit/streamlit_app.py
# Hierarchy: streamlit -> web -> youtube -> ingestion -> services -> projects -> airflow
# Path(__file__).parents[6] should be 'airflow' root
project_root = Path(__file__).resolve().parents[6]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import backend services
BACKEND_AVAILABLE = False
IMPORT_ERROR_MSG = None

try:
    # Use full absolute paths so that relative imports within these modules work correctly
    # from projects.services.ingestion.youtube.api_manager import YouTubeAPIManager
    from projects.services.ingestion.youtube.config import DatabaseConfig
    from projects.services.ingestion.youtube.dao import YouTubeDAO
    from projects.services.ingestion.youtube.models import Base
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
    """
    Initialize database tables if they don't exist.

    
    This is called once per app session to ensure all required tables
    (youtube_channels, youtube_videos, youtube_comments, youtube_tracked_channels)
    are created before any queries are run.
    """
    if not BACKEND_AVAILABLE:
        return  # Skip if backend imports failed
    
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
    except Exception as e:
        # Log but don't crash - tables may already exist or DB may be temporarily unavailable
        st.warning(f"⚠️ Could not initialize database tables: {e}")

# Run database initialization on app start
initialize_database()

# ------------------------
# Data Loading Functions
# ------------------------
@st.cache_data(ttl=10)
def load_tracking_statistics():
    """Load overall tracking statistics."""
    engine = get_engine()
    try:
        conn = engine.raw_connection()
        try:
            # Get counts from each table
            stats = {}
            
            # Total channels
            result = pd.read_sql("SELECT COUNT(*) as count FROM youtube_channels", conn)
            stats["total_channels"] = result["count"].iloc[0] if not result.empty else 0
            
            # Tracked channels
            result = pd.read_sql("SELECT COUNT(*) as count FROM youtube_tracked_channels WHERE is_active = true", conn)
            stats["tracked_channels"] = result["count"].iloc[0] if not result.empty else 0
            
            # Total videos
            result = pd.read_sql("SELECT COUNT(*) as count FROM youtube_videos", conn)
            stats["total_videos"] = result["count"].iloc[0] if not result.empty else 0
            
            # Total comments
            result = pd.read_sql("SELECT COUNT(*) as count FROM youtube_comments", conn)
            stats["total_comments"] = result["count"].iloc[0] if not result.empty else 0
            
            return stats
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"⚠️ Could not load statistics: {e}")
        return {"total_channels": 0, "tracked_channels": 0, "total_videos": 0, "total_comments": 0}

@st.cache_data(ttl=10)
def load_tracked_channels():
    """Load tracked channels with details."""
    engine = get_engine()
    try:
        conn = engine.raw_connection()
        try:
            query = """
                SELECT 
                    c.id as channel_id,
                    c.title,
                    c.thumbnail_url,
                    c.subscriber_count,
                    c.video_count,
                    c.view_count,
                    t.last_checked,
                    t.last_video_published,
                    t.is_active
                FROM youtube_channels c
                JOIN youtube_tracked_channels t ON c.id = t.channel_id
                WHERE t.is_active = true
                ORDER BY t.last_checked DESC
            """
            df = pd.read_sql(query, conn)
            return df
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"⚠️ Could not load tracked channels: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def load_recent_videos(limit: int = 20):
    """Load recent videos from all channels."""
    engine = get_engine()
    try:
        conn = engine.raw_connection()
        try:
            query = f"""
                SELECT 
                    v.id,
                    v.title,
                    v.channel_id,
                    c.title as channel_title,
                    v.thumbnail_url,
                    v.published_at,
                    v.view_count,
                    v.like_count,
                    v.comment_count
                FROM youtube_videos v
                LEFT JOIN youtube_channels c ON v.channel_id = c.id
                ORDER BY v.published_at DESC
                LIMIT {limit}
            """
            df = pd.read_sql(query, conn)
            return df
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"⚠️ Could not load videos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def load_recent_comments(limit: int = 50):
    """Load recent comments from all videos."""
    engine = get_engine()
    try:
        conn = engine.raw_connection()
        try:
            query = f"""
                SELECT 
                    cm.id,
                    cm.video_id,
                    v.title as video_title,
                    cm.author_display_name,
                    cm.text,
                    cm.like_count,
                    cm.published_at,
                    cm.reply_count
                FROM youtube_comments cm
                LEFT JOIN youtube_videos v ON cm.video_id = v.id
                ORDER BY cm.published_at DESC
                LIMIT {limit}
            """
            df = pd.read_sql(query, conn)
            return df
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"⚠️ Could not load comments: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def load_all_channels():
    """Load all channels from database."""
    engine = get_engine()
    try:
        conn = engine.raw_connection()
        try:
            query = """
                SELECT 
                    c.id,
                    c.title,
                    c.subscriber_count,
                    c.video_count,
                    c.view_count,
                    c.country,
                    c.is_tracked,
                    c.last_checked,
                    c.created_at
                FROM youtube_channels c
                ORDER BY c.created_at DESC
            """
            df = pd.read_sql(query, conn)
            return df
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"⚠️ Could not load channels: {e}")
        return pd.DataFrame()


# ------------------------
# Backend Initialization
# ------------------------
@st.cache_resource
def get_dao():
    """Initialize and cache the YouTube DAO."""
    try:
        if not BACKEND_AVAILABLE:
            st.error("❌ Backend services not found. Please check your python path.")
            return None
            
        # Initialize configs
        try:
            db_config = DatabaseConfig.from_env()
        except ValueError as e:
            st.error(f"❌ Configuration error: {e}")
            return None
            
        # Initialize DAO
        dao = YouTubeDAO(db_config)
        return dao
    except Exception as e:
        st.error(f"❌ Failed to initialize backend: {e}")
        return None

# ------------------------
# Action Handlers
# ------------------------
def handle_add_channel(dao: 'YouTubeDAO', channel_id: str):
    """Handle adding a new channel."""
    if not channel_id:
        st.warning("⚠️ Please enter a channel ID")
        return

    with st.spinner(f"Adding channel {channel_id}..."):
        try:
            # Only register in DB, let the background workers handle ingestion
            dao.register_tracked_channel(channel_id)
            st.success(f"✅ Channel {channel_id} added and tracked successfully! Data will appear after ingestion.")
            # Invalidate caches to refresh data
            load_tracking_statistics.clear()
            load_tracked_channels.clear()
            load_all_channels.clear()
        except Exception as e:
            st.error(f"❌ Failed to add channel: {e}")

def handle_remove_channel(dao: 'YouTubeDAO', channel_id: str):
    """Handle removing a tracked channel."""
    try:
        # We only stop tracking, we don't delete data to preserve history
        dao.unregister_tracked_channel(channel_id)
        st.success(f"✅ Channel {channel_id} untracked successfully!")
        # Invalidate caches
        load_tracking_statistics.clear()
        load_tracked_channels.clear()
        load_all_channels.clear()
    except Exception as e:
        st.error(f"❌ Failed to remove channel: {e}")

# ------------------------
# Auto-refresh Logic
# ------------------------
# Using st.fragment for efficient partial reruns (requires Streamlit 1.37+)
@st.fragment(run_every=10)
def render_dashboard():
    # ------------------------
    # Statistics Overview
    # ------------------------
    st.subheader("📊 Tracking Statistics")
    
    stats = load_tracking_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Channels", stats["total_channels"])
    with col2:
        st.metric("Tracked Channels", stats["tracked_channels"])
    with col3:
        st.metric("Total Videos", stats["total_videos"])
    with col4:
        st.metric("Total Comments", stats["total_comments"])
    
    st.divider()
    
    # ------------------------
    # Tabs for different views
    # ------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Tracked Channels", "🎬 Recent Videos", "💬 Recent Comments", "📋 All Channels", "⚙️ Manage Channels"])
    
    with tab1:
        st.subheader("🎯 Tracked Channels")
        
        tracked_df = load_tracked_channels()
        
        if tracked_df.empty:
            st.info("📭 No channels are currently being tracked. Use the 'Manage Channels' tab to add one.")
        else:
            # Display as cards
            for idx, row in tracked_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 2])
                    
                    with col1:
                        if row["thumbnail_url"]:
                            st.image(row["thumbnail_url"], width=80)
                        else:
                            st.write("📺")
                    
                    with col2:
                        st.markdown(f"**{row['title']}**")
                        st.caption(f"Channel ID: `{row['channel_id']}`")
                    
                    with col3:
                        sub_count = row["subscriber_count"]
                        if sub_count >= 1_000_000:
                            sub_display = f"{sub_count / 1_000_000:.1f}M"
                        elif sub_count >= 1_000:
                            sub_display = f"{sub_count / 1_000:.1f}K"
                        else:
                            sub_display = str(sub_count)
                        
                        st.write(f"👥 {sub_display} subscribers | 📹 {row['video_count']} videos")
                        
                        if row["last_checked"]:
                            last_checked = pd.to_datetime(row["last_checked"])
                            st.caption(f"Last checked: {last_checked.strftime('%Y-%m-%d %H:%M')}")
                    
                    st.divider()
    
    with tab2:
        st.subheader("🎬 Recent Videos")
        
        # Move slider outside fragment if we want it to NOT reset, however inside fragment it persists if key is stable.
        # But for strictly correct state management, inputs inside fragments are fine.
        video_limit = st.slider("Number of videos to display", 5, 50, 20, key="video_limit")
        videos_df = load_recent_videos(video_limit)
        
        if videos_df.empty:
            st.info("📭 No videos found in the database.")
        else:
            # Visualization: Video engagement
            if len(videos_df) > 1:
                fig = px.bar(
                    videos_df.head(10),
                    x="title",
                    y=["view_count", "like_count", "comment_count"],
                    title="Top 10 Videos Engagement",
                    barmode="group",
                    labels={"value": "Count", "title": "Video Title"}
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                fig.update_xaxes(ticktext=[t[:30] + "..." if len(t) > 30 else t for t in videos_df.head(10)["title"]], tickvals=videos_df.head(10)["title"])
                st.plotly_chart(fig, use_container_width=True)
            
            # Display as table
            display_df = videos_df[["title", "channel_title", "view_count", "like_count", "comment_count", "published_at"]].copy()
            display_df.columns = ["Title", "Channel", "Views", "Likes", "Comments", "Published"]
            st.dataframe(display_df)
    
    with tab3:
        st.subheader("💬 Recent Comments")
        
        comment_limit = st.slider("Number of comments to display", 10, 100, 50, key="comment_limit")
        comments_df = load_recent_comments(comment_limit)
        
        if comments_df.empty:
            st.info("📭 No comments found in the database.")
        else:
            # Display comments
            for idx, row in comments_df.head(20).iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{row['author_display_name']}** on *{row['video_title'][:50]}...*")
                        comment_text = row["text"][:300] + "..." if len(row["text"]) > 300 else row["text"]
                        st.write(comment_text)
                    
                    with col2:
                        st.write(f"👍 {row['like_count']} | 💬 {row['reply_count']} replies")
                        if row["published_at"]:
                            published = pd.to_datetime(row["published_at"])
                            st.caption(published.strftime("%Y-%m-%d %H:%M"))
                    
                    st.divider()
    
    with tab4:
        st.subheader("📋 All Channels")
        
        all_channels_df = load_all_channels()
        
        if all_channels_df.empty:
            st.info("📭 No channels in the database. Use the YouTube ingestion service to add channels.")
        else:
            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                show_tracked_only = st.checkbox("Show tracked only", value=False)
            with col2:
                search = st.text_input("Search by title", "")
            
            filtered_df = all_channels_df.copy()
            
            if show_tracked_only:
                filtered_df = filtered_df[filtered_df["is_tracked"] == True]
            
            if search:
                filtered_df = filtered_df[filtered_df["title"].str.contains(search, case=False, na=False)]
            
            # Display as table
            display_df = filtered_df[["title", "subscriber_count", "video_count", "view_count", "country", "is_tracked"]].copy()
            # Ensure numeric columns are properly typed to avoid Streamlit TypeError
            display_df["subscriber_count"] = pd.to_numeric(display_df["subscriber_count"], errors='coerce').fillna(0).astype(int)
            display_df["video_count"] = pd.to_numeric(display_df["video_count"], errors='coerce').fillna(0).astype(int)
            display_df["view_count"] = pd.to_numeric(display_df["view_count"], errors='coerce').fillna(0).astype(int)
            display_df.columns = ["Title", "Subscribers", "Videos", "Views", "Country", "Tracked"]
            st.dataframe(display_df)
            
            # Visualization: Subscriber distribution
            if len(filtered_df) > 1:
                fig = px.pie(
                    filtered_df.head(10),
                    values="subscriber_count",
                    names="title",
                    title="Subscriber Distribution (Top 10 Channels)"
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader("⚙️ Manage Channels")
        
        dao = get_dao()
        if not dao:
            st.error("Backend unavailable. Cannot manage channels.")
        else:
            st.markdown("#### Add New Channel")
            with st.form("add_channel_form"):
                new_channel_id = st.text_input("YouTube Channel ID", placeholder="e.g. UC_x5XG1OV2P6uZZ5FSM9Ttw")
                submitted = st.form_submit_button("Add Channel")
                if submitted:
                    handle_add_channel(dao, new_channel_id)
            
            st.divider()
            
            st.markdown("#### Remove Tracked Channel")
            tracked_active_df = load_tracked_channels()
            if tracked_active_df.empty:
                 st.info("No tracked channels to remove.")
            else:
                for idx, row in tracked_active_df.iterrows():
                    col1, col2, col3 = st.columns([1, 4, 2])
                    with col1:
                         if row["thumbnail_url"]:
                            st.image(row["thumbnail_url"], width=40)
                    with col2:
                        st.write(f"**{row['title']}** ({row['channel_id']})")
                    with col3:
                         if st.button("Stop Tracking", key=f"remove_{row['channel_id']}"):
                             handle_remove_channel(dao, row['channel_id'])
    
    st.divider()
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')} | SE363 Social Listening Platform")

# ------------------------
# Main Dashboard
# ------------------------
st.title("📺 YouTube Monitor Dashboard")
st.markdown("Real-time monitoring of YouTube channel tracking and scraped data.")

# Render the dashboard fragment
render_dashboard()