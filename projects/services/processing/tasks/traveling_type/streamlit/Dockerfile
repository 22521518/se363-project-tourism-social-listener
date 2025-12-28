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

WORKDIR /opt/airflow/projects/services/processing/tasks/traveling_type

# Create a virtual environment and ensure pip is available
RUN python -m venv /opt/monitor_traveling_type_venv
ENV EXTRACT_TRAVELING_TYPE_VENV="/opt/monitor_traveling_type_venv"
ENV PATH="$EXTRACT_TRAVELING_TYPE_VENV/bin:$PATH"

# Copy minimal requirements and install into the venv
COPY projects/services//processing/tasks/traveling_type/streamlit/requirements.txt /tmp/traveling_type/requirements.txt

# Use the venv's python -m pip explicitly to avoid PATH ordering assumptions
RUN $EXTRACT_TRAVELING_TYPE_VENV/bin/python -m pip install --upgrade pip setuptools wheel \
	&& $EXTRACT_TRAVELING_TYPE_VENV/bin/pip install -r /tmp/traveling_type/requirements.txt \
	&& rm /tmp/traveling_type/requirements.txt

# Expose Streamlit port
EXPOSE 8503

# Default CMD to run streamlit
CMD ["$EXTRACT_TRAVELING_TYPE_VENV/bin/streamlit", "run", "streamlit_app.py", "--server.port", "8504", "--server.address", "0.0.0.0"]
