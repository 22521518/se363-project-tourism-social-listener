FROM python:3.10-slim

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

WORKDIR /opt/airflow/projects/frontend/web/streamlit

# Create a virtual environment and ensure pip is available
RUN python -m venv /opt/streamlit_venv
ENV VIRTUAL_ENV="/opt/streamlit_venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy entrypoint script that activates the venv and optionally waits for Postgres
COPY projects/frontend/web/streamlit/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy minimal requirements and install into the venv
COPY projects/frontend/web/streamlit/requirements.txt /tmp/requirements.txt
# Use the venv's python -m pip explicitly to avoid PATH ordering assumptions
RUN /opt/streamlit_venv/bin/python -m pip install --upgrade pip setuptools wheel \
	&& /opt/streamlit_venv/bin/pip install -r /tmp/requirements.txt \
	&& rm /tmp/requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Default entrypoint will ensure venv is used; CMD provides default Streamlit args
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
