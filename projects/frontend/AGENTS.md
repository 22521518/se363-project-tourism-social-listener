# Frontend – Agent Guidelines

## Module Overview

UI components and dashboards for exploring mentions, trends, and alerts.

## Commands

```powershell
# Streamlit dashboard
cd web/streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py

# React (when implemented)
cd web/react
npm install
npm run dev
```

## Code Style

### Python (Streamlit)
- Follow PEP 8
- Use type hints
- Keep dashboard components modular

### React (planned)
- TypeScript strict mode
- Functional components with hooks
- Domain-based folder structure: `src/domains/<feature>/`

## Testing

```powershell
# Python
pytest tests/

# React
npm test
```

## Commit Scope

- One component or feature per commit
- Include screenshots for UI changes
- Link to API contract when adding data-fetching features
