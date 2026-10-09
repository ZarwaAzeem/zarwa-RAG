# Starts both services, each in its own window.
#   Backend  (FastAPI) -> http://localhost:8080
#   Frontend (React)   -> http://localhost:5173
$root = $PSScriptRoot

Start-Process powershell -WorkingDirectory "$root\backend" -ArgumentList @(
    '-NoExit', '-Command',
    '& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8080'
)

Start-Process powershell -WorkingDirectory "$root\frontend" -ArgumentList @(
    '-NoExit', '-Command', 'npm run dev'
)
