FROM python:3.12-slim

# keep layers small and install build deps for psycopg2
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies for psycopg2 + runtime libpq5
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       libpq5 \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/airflow/projects/services/ingestion/youtube

# Create a virtual environment and ensure pip is available
RUN python -m venv /opt/monitor_youtube_venv
ENV MONITOR_YOUTUBE_VENV="/opt/monitor_youtube_venv"
ENV PATH="$MONITOR_YOUTUBE_VENV/bin:$PATH"

# Copy minimal requirements and install into the venv
COPY projects/services/ingestion/youtube/requirements.monitor.txt /tmp/youtube/requirements.txt

# Use the venv's python -m pip explicitly to avoid PATH ordering assumptions
RUN $MONITOR_YOUTUBE_VENV/bin/python -m pip install --upgrade pip setuptools wheel \
	&& $MONITOR_YOUTUBE_VENV/bin/pip install -r /tmp/youtube/requirements.txt \
	&& rm /tmp/youtube/requirements.txt

# Expose Streamlit port
EXPOSE 8502

# Default CMD to run streamlit
CMD ["$MONITOR_YOUTUBE_VENV/bin/streamlit", "run", "streamlit_app.py", "--server.port", "8502", "--server.address", "0.0.0.0"]
