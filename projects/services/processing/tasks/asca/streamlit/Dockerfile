# ASCA Streamlit Monitoring App
# ================================
# Runs the ASCA monitoring web interface on port 8152
#
# Build:
#   docker build -t asca-streamlit .
#
# Run:
#   docker run -p 8152:8152 --env-file ../.env asca-streamlit

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy ASCA module for imports (parent directories)
# Note: In docker-compose, we mount the full project instead

# Set Python path for module imports
ENV PYTHONPATH=/opt/airflow

# Expose port
EXPOSE 8152

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8152/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8152", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
