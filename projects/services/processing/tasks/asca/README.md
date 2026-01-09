# ASCA Processing Module

Aspect Category Sentiment Analysis (ASCA) processing module cho Airflow pipeline.

## Tính năng

- **ASCA Extraction**: Phân tích aspect-sentiment từ text (6 categories, 3 sentiments)
- **Batch Processing**: Xử lý batch lớn với Kafka và Spark Streaming
- **Language Detection**: Tự động detect Vietnamese vs English
- **Human Approval**: Review và approve extractions qua Streamlit UI
- **Model Retraining**: Export approved records, retrain, và compare performance

## Categories & Sentiments

| Categories | Sentiments |
|-----------|------------|
| LOCATION | positive |
| PRICE | negative |
| ACCOMMODATION | neutral |
| FOOD | |
| SERVICE | |
| AMBIENCE | |

## Quick Start

### 1. Setup Environment

```bash
cd projects/services/processing/tasks/asca

# Create virtual environment
./scripts/setup_venv.sh

# Copy và configure .env
cp .env.example .env
# Edit .env with your values
```

### 2. Run Kafka Consumer

```bash
./scripts/run_consumer.sh
```

### 3. Run Streamlit UI

```bash
cd streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py --server.port 8152
```

Or with Docker:

```bash
docker-compose -f docker-compose.asca.yaml up -d
# Access at http://localhost:8152
```

## Directory Structure

```
asca/
├── config/         # Settings và configuration
├── dto/            # Data Transfer Objects
├── orm/            # SQLAlchemy models
├── dao/            # Data Access Objects
├── pipelines/      # ASCA extraction pipeline
├── batch/          # Batch processing
├── utils/          # Export utilities
├── messaging/      # Kafka consumer/producer
├── scripts/        # Shell scripts
├── streamlit/      # Web UI
├── requirements.txt
├── .env.example
└── docker-compose.asca.yaml
```

## Kafka Topics

| Topic | Description |
|-------|-------------|
| `asca-input` | Input messages for processing |
| `asca-output` | Extraction results |

## Airflow DAGs

| DAG | Schedule | Description |
|-----|----------|-------------|
| `asca_streaming_producer_dag` | Every hour | Stream YouTube comments from DB → Kafka |
| `asca_consumer_dag` | Every 30 min | Run raw Kafka consumer to process |
| `asca_spark_consumer_dag` | Daily | Run Spark Streaming consumer |
| `asca_training_dag` | Weekly | Export → Train → Compare → Update |

### Data Flow

```
[DB: youtube_comments] 
        ↓
[asca_streaming_producer_dag]
        ↓
[Kafka: asca-input]
        ↓
[asca_consumer_dag]
        ↓
[DB: asca_extractions]
```

## Environment Variables

```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=airflow
DB_PASSWORD=airflow
DB_NAME=airflow

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_ASCA_INPUT=asca-input
KAFKA_TOPIC_ASCA_OUTPUT=asca-output

# ASCA
ASCA_MODEL_PATH=/opt/airflow/models/asca/acsa.pkl
ASCA_LANGUAGE=vi
ASCA_AUTO_DETECT_LANGUAGE=true
```

## API Usage

```python
from projects.services.processing.tasks.asca.pipelines import ASCAExtractionPipeline
from projects.services.processing.tasks.asca.dto import UnifiedTextEvent

# Create pipeline
pipeline = ASCAExtractionPipeline()

# Process single text
event = UnifiedTextEvent(
    source="youtube",
    source_type="comment",
    external_id="test1",
    text="Phòng sạch sẽ, nhân viên thân thiện"
)
result = pipeline.process(event)

# Output: [AspectSentiment(category='ACCOMMODATION', sentiment='positive'), ...]
print(result.aspects)
```

---

## Local Testing (Không cần venv)

### Step 1: Set Environment Variables

**Windows CMD:**
```cmd
set DB_HOST=localhost
set DB_PORT=5432
set DB_USER=airflow
set DB_PASSWORD=airflow
set DB_NAME=airflow
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set KAFKA_TOPIC_ASCA_INPUT=asca-input
set KAFKA_TOPIC_ASCA_OUTPUT=asca-output
set ASCA_MODEL_PATH=d:/Code/SE363/nlp/asca/models/acsa.pkl
set ASCA_LANGUAGE=vi
set PYTHONPATH=d:\Code\SE363\course\airflow_tutor\airflow-c\airflow
```

**PowerShell:**
```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_USER="airflow"
$env:DB_PASSWORD="airflow"
$env:DB_NAME="airflow"
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
$env:ASCA_MODEL_PATH="d:/Code/SE363/nlp/asca/models/acsa.pkl"
$env:PYTHONPATH="d:\Code\SE363\course\airflow_tutor\airflow-c\airflow"
```

### Step 2: Install Dependencies

```bash
pip install pydantic pydantic-settings sqlalchemy psycopg2-binary kafka-python-ng python-dotenv pandas
```

### Step 3: Test Components

**Test Config + Language Detection:**
```bash
cd d:\Code\SE363\course\airflow_tutor\airflow-c\airflow

python -c "from projects.services.processing.tasks.asca.config import settings, detect_language; print(f'Language detect: {detect_language(\"Phòng sạch sẽ\")}')"
```

**Test DTO Imports:**
```bash
python -c "from projects.services.processing.tasks.asca.dto import UnifiedTextEvent, ASCAExtractionResult; print('DTO OK')"
```

**Test DAO (requires Postgres running):**
```bash
python -c "
from projects.services.processing.tasks.asca.config.settings import DatabaseConfig
from projects.services.processing.tasks.asca.dao.dao import ASCAExtractionDAO
config = DatabaseConfig.from_env()
print(f'Connection: {config.connection_string}')
dao = ASCAExtractionDAO(config)
print('DAO + DB OK')
"
```

**Test Pipeline (requires ASCA model):**
```bash
python -c "
from projects.services.processing.tasks.asca.pipelines import ASCAExtractionPipeline
from projects.services.processing.tasks.asca.dto import UnifiedTextEvent
pipeline = ASCAExtractionPipeline()
event = UnifiedTextEvent(source='test', source_type='comment', external_id='t1', text='Phòng sạch sẽ')
result = pipeline.process(event)
print(f'Aspects: {result.aspects}')
"
```

### Step 4: Run Consumer (Mock Mode)

```bash
cd d:\Code\SE363\course\airflow_tutor\airflow-c\airflow

# Mock mode (không cần ASCA model)
python -m projects.services.processing.tasks.asca.messaging.consumer --no-pipeline --max-messages 5

# Full mode (requires Kafka + Postgres + ASCA model)
python -m projects.services.processing.tasks.asca.messaging.consumer --max-messages 10
```

### Step 5: Run Batch Processor

```bash
python -m projects.services.processing.tasks.asca.batch.batch_processor --batch-size 10 --max-records 50
```

### Step 6: Run Streaming Producer (DB → Kafka)

```bash
# Run once (send one batch and exit)
python -m projects.services.processing.tasks.asca.streaming.youtube_streaming_producer --once

# Continuous streaming mode
python -m projects.services.processing.tasks.asca.streaming.youtube_streaming_producer --interval 10

# With max messages limit
python -m projects.services.processing.tasks.asca.streaming.youtube_streaming_producer --max-messages 500
```

### Step 7: Run Streamlit UI

```bash
cd d:\Code\SE363\course\airflow_tutor\airflow-c\airflow\projects\services\processing\tasks\asca\streamlit

pip install streamlit pandas plotly
streamlit run streamlit_app.py --server.port 8152
```

> **Note:** Consumer và Streaming Producer cần Postgres + Kafka running. Pipeline cần ASCA model file.

---

## License

Internal use only.
