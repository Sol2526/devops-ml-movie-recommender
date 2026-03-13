# DevOps ML Movie Recommender

A backend first personal project built with Python and FastAPI.

The goal of this project is to build a movie recommendation app that starts with survey based preferences and improves over time through user feedback such as:

- Seen
- Watch Again
- Bad Pick

I’m also building this project as a hands on way to practice DevOps concepts and pipeline workflows all while working on a real application.

## Current Features

- FastAPI backend
- TMDb API integration
- Survey-based user preferences
- Recommendation preview logic
- Feedback buckets
- SQLite persistence
- Docker support
- Docker Compose support
- Automated tests with pytest

## Tech Stack

- Python
- FastAPI
- SQLModel
- SQLite
- Pytest
- Docker
- Docker Compose

## Current Status

This project is currently backend-first.

At the moment, the main interface is FastAPI Swagger UI, which can be used to test the API and recommendation flow.

## Planned Next Steps

- GitHub Actions CI
- Lightweight frontend
- Stronger recommendation logic
- More feedback-driven personalization
- Later ML improvements

## Run Locally

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Add environment variables

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key_here
```

### 4. Run the app

```powershell
python -m uvicorn app.main:app --reload
```

### Then open:

- `http://127.0.0.1:8000/docs`

## Run with Docker

### Build and run with Docker

```powershell
docker build -t devops-ml-movie-recommender .
docker run --env-file .env -p 8000:8000 devops-ml-movie-recommender
```

Then open:

- `http://127.0.0.1:8000/docs`

## Run with Docker Compose

```powershell
docker compose up --build
```

Then open:

- `http://127.0.0.1:8000/docs`

## Notes

This project is currently backend first, and the main interface right now is FastAPI Swagger UI.

The goal is to keep building it into a more complete recommendation system with:

- stronger feedback recommendation logic
- GitHub Actions CI
- a lightweight frontend
- later ML improvements
