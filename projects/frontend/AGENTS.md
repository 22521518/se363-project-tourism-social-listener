# Frontend – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps
1. Plan in `agents_plans/tasks/`
2. Implement component/feature
3. Test and include screenshots for UI changes

## Commands
```powershell
# Streamlit dashboard
cd web/streamlit && streamlit run streamlit_app.py

# React (when implemented)
cd web/react && npm install && npm run dev
```

## Testing
```powershell
pytest tests/   # Python
npm test        # React
```

## Style
- Python: PEP 8, type hints, modular components
- React: TypeScript strict, functional components

