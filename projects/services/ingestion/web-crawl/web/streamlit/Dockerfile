# Web Crawl Monitor Streamlit App
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY streamlit_app.py .

# Expose Streamlit port
EXPOSE 8151

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8151/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8151", "--server.address=0.0.0.0"]
