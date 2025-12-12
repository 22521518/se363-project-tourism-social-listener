# YouTube Monitor Dashboard

A Streamlit dashboard for monitoring YouTube channel tracking and scraped data from the Social Listening platform.

## Features

| Feature | Description |
|---------|-------------|
| **Tracking Statistics** | Overview metrics for channels, videos, and comments |
| **Tracked Channels** | View actively monitored channels with status |
| **Recent Videos** | Browse latest scraped videos with engagement metrics |
| **Recent Comments** | View recent comments from tracked videos |
| **Visualizations** | Plotly charts for engagement and subscriber data |
| **Auto-refresh** | Updates every 10 seconds automatically |

## Quick Start

```powershell
cd d:\Code\SE363\course\airflow_tutor\airflow-c\airflow\projects\frontend\web\streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Navigate to the **YouTube Monitor** page in the sidebar.

## Database Requirements

This dashboard requires the following PostgreSQL tables:

| Table | Description |
|-------|-------------|
| `youtube_channels` | Channel metadata |
| `youtube_videos` | Video data |
| `youtube_comments` | Comment content |
| `youtube_tracked_channels` | Tracking state |

Tables are created by the YouTube ingestion service (`projects/services/ingestion/youtube/`).

## Configuration

By default, connects to Docker PostgreSQL (`host: postgres`).

For local development, edit `DB_CONFIG` in `pages/youtube_monitor.py`:

```python
DB_CONFIG = {
    "host": "localhost",  # Changed from 'postgres'
    ...
}
```

## Related Services

- **YouTube API Manager**: `projects/services/ingestion/youtube/api_manager.py`
- **Tracking Manager**: `projects/services/ingestion/youtube/tracking_manager.py`
- **DAO/Models**: `projects/services/ingestion/youtube/dao.py`, `models.py`
