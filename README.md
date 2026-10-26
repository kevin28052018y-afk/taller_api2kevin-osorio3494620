# Mi FastAPI Project

Backend en FastAPI + MongoDB Atlas (Motor) y frontend estático.

```
backend/   -> API FastAPI (app/core, app/db, app/models, app/routers)
frontend/  -> index.html que consume la API
```

## Puesta en marcha (Windows PowerShell)

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # luego edita .env con tu URL de MongoDB Atlas
uvicorn app.main:app --reload
```

- Docs: http://127.0.0.1:8000/docs
- Frontend: abre `frontend/index.html` o corre `python -m http.server 5500` dentro de `frontend/`
