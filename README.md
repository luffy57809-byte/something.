# Chesslytic

Chess game analysis for chess.com and Lichess games: move classification, accuracy, puzzles built from your own mistakes, and a cheat-detection check.

## Layout
- `chess_coach/` FastAPI backend: Stockfish analysis, stats, puzzles, accounts
- `chess_detector/` cheat-detection scoring
- `frontend/` React app (create-react-app)
- `main.py` backend entry point; `install_stockfish.sh` downloads Stockfish into `bin/`

## Run locally
    pip install -r requirements.txt
    bash install_stockfish.sh
    python -m uvicorn main:app --host 0.0.0.0 --port 8000

In a second terminal:

    cd frontend && npm install && npm start

## Settings (environment variables; never commit them)
- `DATABASE_URL` Postgres connection string (a local SQLite file is used if unset)
- `JWT_SECRET` signing key for login tokens
- `FRONTEND_URL` public address of the frontend, used in emailed links
- `BREVO_API_KEY` and `BREVO_SENDER_EMAIL` turn on email verification and password reset (off if unset)
- `REACT_APP_API_URL` optional backend address for the frontend build

## Tests
    python -m unittest discover -s tests -t . -v
