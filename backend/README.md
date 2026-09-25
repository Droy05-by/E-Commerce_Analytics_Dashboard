# Backend API

The backend is built with FastAPI and serves both the analytical endpoints and the SQLite data layer for the E-Commerce Sales & Customer Intelligence Dashboard.

## Key Responsibilities

- Load and validate uploaded CSV files
- Store transactions in SQLite
- Calculate business KPIs and analytics using Pandas and NumPy
- Run customer segmentation, RFM, and forecasting logic
- Serve data for the React frontend

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

## API Docs

Once running, visit:
- http://localhost:8000/docs
- http://localhost:8000/redoc
