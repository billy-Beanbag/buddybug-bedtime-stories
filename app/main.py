from pathlib import Path
import itertools
from typing import List, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from . import config


app = FastAPI(title=config.APP_NAME)

# In-memory todo store for demo purposes
_id_counter = itertools.count(1)
_todos: List[Dict[str, Any]] = []


class TodoCreate(BaseModel):
	title: str


@app.get("/api/health")
def health() -> Dict[str, str]:
	return {"status": "ok", "app": config.APP_NAME}


@app.get("/api/todos")
def list_todos() -> Dict[str, Any]:
	return {"items": _todos}


@app.post("/api/todos", status_code=201)
def create_todo(todo: TodoCreate) -> Dict[str, Any]:
	item = {"id": next(_id_counter), "title": todo.title, "done": False}
	_todos.append(item)
	return item


# Serve static frontend
project_root = Path(__file__).resolve().parents[1]
frontend_dir = project_root / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")




