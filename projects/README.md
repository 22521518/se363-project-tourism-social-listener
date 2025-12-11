# Social Listening for Tourism

A real-time social listening and sentiment analysis platform built for the SE363 course (Big Data Application Development) at UIT-VNU-HCM.

## Overview

This project collects public social media data, processes it through an event-driven pipeline, and surfaces sentiment insights via an interactive dashboard. The current focus is **Aspect-Based Sentiment Analysis (ABSA)** for tourism-related conversations.

**Key capabilities:**
- Real-time data ingestion from social platforms (YouTube first)
- NLP enrichment: sentiment, topics, entity extraction
- Aggregated analytics and trend detection
- Interactive Streamlit dashboard

## Quick Start

### Run the Dashboard

```powershell
cd frontend/web/streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py
```

> **Note:** The dashboard requires a running PostgreSQL instance with ABSA results. See the Streamlit app configuration for connection details.

## Project Structure

```
projects/
├── api/                 # API service (delivery layer)
├── data/                # Data storage (raw, processed, models)
├── frontend/            # Dashboard and visualizations
│   └── web/streamlit/   # Current working Streamlit dashboard
├── libs/                # Shared types and contracts
├── services/            # Domain services
│   ├── aggregator/      # Metrics computation
│   ├── ingestion/       # Social platform connectors
│   ├── nlp/             # Sentiment and topic extraction
│   └── processing/      # Data cleaning and normalization
└── agents_plans/        # Work planning and tracking
```

## Tech Stack

| Layer       | Technology                                    |
|-------------|-----------------------------------------------|
| Ingestion   | Python, YouTube API                           |
| Messaging   | Apache Kafka                                  |
| Processing  | Apache Spark                                  |
| Storage     | PostgreSQL, OpenSearch (planned)              |
| NLP         | Google Gemini / Vertex AI, VADER, spaCy       |
| Dashboard   | Streamlit, Plotly                             |
| API         | Node.js / Express (planned)                   |

## Contributing

1. Read the module-level `README.md` in each subdirectory for responsibilities and boundaries
2. Follow the planning workflow in `agents_plans/`
3. See `AGENTS.md` for code style, commit guidelines, and agent-specific conventions
