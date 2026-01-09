FROM apache/airflow:2.9.0

USER root

# Cài Java (cho Spark)
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    git \
    curl \
    unzip \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libnspr4 \
    libxkbcommon0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Download VnCoreNLP for Vietnamese NLP
RUN mkdir -p /opt/airflow/VnCoreNLP-1.2 && \
    curl -L -o /tmp/vncorenlp.zip "https://github.com/vncorenlp/VnCoreNLP/archive/refs/tags/v1.2.zip" && \
    unzip -q /tmp/vncorenlp.zip -d /tmp && \
    cp -r /tmp/VnCoreNLP-1.2/* /opt/airflow/VnCoreNLP-1.2/ && \
    rm -rf /tmp/vncorenlp.zip /tmp/VnCoreNLP-1.2 && \
    chown -R airflow:root /opt/airflow/VnCoreNLP-1.2

ENV VNCORENLP_PATH=/opt/airflow/VnCoreNLP-1.2/VnCoreNLP-1.2.jar


# Copy file requirements trong chính thư mục base
COPY base/requirements.txt /tmp/base_requirements.txt

USER airflow
RUN pip install --no-cache-dir -r /tmp/base_requirements.txt && \
    # Fix lỗi kafka.vendor.six.moves không tồn tại trong kafka-python 2.0.1
    sed -i "s|from kafka.vendor.six.moves import range|from six.moves import range|" \
        /home/airflow/.local/lib/python3.*/site-packages/kafka/codec.py || true

# ================================
# 🔧 Copy scripts và cấp quyền thực thi (chuẩn reproducible)
# ================================
USER root
COPY projects/ /opt/airflow/projects/
RUN chmod +x /opt/airflow/projects/**/*.sh || true
# RUN sed -i 's/\r$//' /opt/airflow/projects/**/*.sh
RUN find /opt/airflow/projects -type f -name "*.sh" -exec sed -i 's/\r$//' {} +

USER airflow

# Copy thư mục streamlit của project vào image
COPY projects/frontend/web/streamlit /opt/airflow/projects/frontend/web/streamlit

# Cài các thư viện cần thiết cho Streamlit
USER airflow
RUN pip install --no-cache-dir streamlit psycopg2-binary pandas