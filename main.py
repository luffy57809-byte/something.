import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from chess_coach.api import app

frontend_build = os.path.join(os.path.dirname(__file__), "frontend", "build")

@app.get("/app/{full_path:path}")
def serve_react(full_path: str):
    file_path = os.path.join(frontend_build, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_build, "index.html"))

@app.get("/app")
def serve_react_root():
    return FileResponse(os.path.join(frontend_build, "index.html"))

app.mount("/static", StaticFiles(
    directory=os.path.join(frontend_build, "static")), name="static")
