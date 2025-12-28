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

WORKDIR /opt/airflow/projects/services/processing/tasks/intention

# Create a virtual environment and ensure pip is available
RUN python -m venv /opt/monitor_intention_venv
ENV EXTRACT_INTENTION_VENV="/opt/monitor_intention_venv"
ENV PATH="$EXTRACT_INTENTION_VENV/bin:$PATH"

# Copy minimal requirements and install into the venv
COPY projects/services//processing/tasks/intention/streamlit/requirements.txt /tmp/intention/requirements.txt

# Use the venv's python -m pip explicitly to avoid PATH ordering assumptions
RUN $EXTRACT_INTENTION_VENV/bin/python -m pip install --upgrade pip setuptools wheel \
	&& $EXTRACT_INTENTION_VENV/bin/pip install -r /tmp/intention/requirements.txt \
	&& rm /tmp/intention/requirements.txt

# Expose Streamlit port
EXPOSE 8503

# Default CMD to run streamlit
CMD ["$EXTRACT_INTENTION_VENV/bin/streamlit", "run", "streamlit_app.py", "--server.port", "8503", "--server.address", "0.0.0.0"]
