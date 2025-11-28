## My First App (FastAPI + Static Frontend)

This is a minimal, production-friendly starter you can understand, run, and extend.  
Backend uses FastAPI; frontend is a simple static page served by the backend.

### What you get
- FastAPI app with `/api/health` and `/api/todos` (in-memory)
- Static frontend (`frontend/`) mounted at `/`
- Environment variables via `.env` (optional)
- Windows-friendly `run.ps1` to set up and run locally

### Project structure
```
app/
  __init__.py
  config.py
  main.py
frontend/
  index.html
  app.js
  styles.css
.gitignore
requirements.txt
run.ps1
.env (optional, create from .env.example)
```

### Prerequisites
- Windows 10
- Python 3.10+ (`py -3 --version` to check)
- PowerShell 7+ (you are already using it)

### First run (Windows, PowerShell)
1) Open PowerShell in the project folder:
```powershell
cd "C:\Users\User\Documents\my-first-app"
```
2) Create and activate a virtual environment, install deps, and start the server:
```powershell
.\run.ps1 -Install
```
3) Open the app in your browser:
```
http://127.0.0.1:8000
```

### Next runs
```powershell
.\run.ps1
```

### Environment variables
Create a `.env` file in the project root (same folder as `requirements.txt`) to customize settings:
```
APP_NAME=My First App
```
If `.env` is missing, sensible defaults are used.

### Useful CLI alternative (without run.ps1)
If you prefer to run manually:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Notes
- This uses an in-memory todo list for simplicity. On restart, todos reset.
- When you’re ready, we can add a database (SQLite/Postgres), authentication, tests, and deploy scripts.




