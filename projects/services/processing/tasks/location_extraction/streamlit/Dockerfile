
FROM python:3.12-slim

# keep layers small and install build deps for psycopg2
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

# Install build dependencies for psycopg2 + runtime libpq5
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       libpq5 \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/airflow/projects/services/processing/tasks/location_extraction

# Create a virtual environment and ensure pip is available
RUN python -m venv /opt/monitor_location_venv
ENV EXTRACT_LOCATION_VENV="/opt/monitor_location_venv"
ENV PATH="$EXTRACT_LOCATION_VENV/bin:$PATH"

# Copy minimal requirements and install into the venv
COPY projects/services/processing/tasks/location_extraction/streamlit/requirements.txt /tmp/location/requirements.txt

# Use the venv's python -m pip explicitly to avoid PATH ordering assumptions
RUN $EXTRACT_LOCATION_VENV/bin/python -m pip install --upgrade pip setuptools wheel \
	&& $EXTRACT_LOCATION_VENV/bin/pip install -r /tmp/location/requirements.txt \
	&& rm /tmp/location/requirements.txt

# Expose Streamlit port
EXPOSE 8150

# Default CMD to run streamlit
CMD ["$EXTRACT_LOCATION_VENV/bin/streamlit", "run", "streamlit/streamlit_app.py", "--server.port", "8150", "--server.address", "0.0.0.0"]
