# Zarwa's Resume Chatbot (RAG)

A chatbot that answers visitors' questions about Zarwa Azeem, grounded in the resume. Two services:

| Service  | Stack                                       | Port |
| -------- | ------------------------------------------- | ---- |
| frontend | React + Vite                                | 5173 |
| backend  | FastAPI, sentence-transformers, FAISS       | 8080 |

## How it works

```
ZarwaAzeem-Resume.pdf
   │  data acquisition   backend/app/acquisition.py   extract text, split into section-aware chunks
   ▼
sentence-transformer    backend/app/embeddings.py    all-MiniLM-L6-v2, normalised vectors
   ▼
FAISS vector DB         backend/app/vector_store.py  IndexFlatIP (cosine), saved to backend/storage/
   ▼
question → top-k chunks → answer                      backend/app/generator.py
```

**Always up to date.** A watcher thread (`backend/app/pipeline.py`) hashes the source
documents every 3 seconds. Replace the resume PDF, or drop extra `.pdf` / `.txt` / `.md`
files into `backend/data/`, and the index is rebuilt and swapped in without a restart.

**Answers.** With `ANTHROPIC_API_KEY` set in `backend/.env`, Claude writes the answer from the
retrieved chunks. Without a key the bot replies with the matching resume passages directly.

**Admin page.** Type `zarwo` anywhere in the app to open it and attach a new resume PDF.
The upload replaces `ZarwaAzeem-Resume.pdf` (the previous file is copied to
`backend/resume-backups/`) and the index is rebuilt straight away. The code only hides the
page; the upload endpoint itself has no password.

**Private chats.** Each page load gets its own random session id from the backend. Chat
history is held in memory under that id (`backend/app/sessions.py`), is only ever read back
for the session that wrote it, and is never saved in the browser, so visitors cannot see each
other's chats and every reload starts clean.

## Run

First-time setup:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\frontend
npm install
```

Start both services:

```powershell
.\start.ps1
```

or one at a time:

```powershell
# backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8080

# frontend
cd frontend
npm run dev
```

Then open http://localhost:5173.

## API

| Method | Path           | Purpose                                             |
| ------ | -------------- | --------------------------------------------------- |
| POST   | `/api/session` | Start a private visitor session → `{ session_id }`  |
| POST   | `/api/chat`    | `{ message, conversation_id }` + `X-Session-Id` header → `{ answer, sources, mode }` |
| GET    | `/api/status`  | Index state: chunk count, sources, last indexed     |
| POST   | `/api/reindex` | Force a rebuild (the watcher normally handles this) |
| POST   | `/api/admin/resume` | Replace the resume (PDF as the request body)   |
| GET    | `/health`      | Liveness                                            |

Interactive docs: http://localhost:8080/docs
