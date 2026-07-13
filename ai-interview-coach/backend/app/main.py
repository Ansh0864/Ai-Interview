import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import session, history

app = FastAPI(title="AI Interview Coach", version="0.1.0")

# ALLOWED_ORIGINS env var: comma-separated list of EXACT origins, e.g.
# "https://your-app.vercel.app,http://localhost:5173"
# Falls back to local dev origins if unset.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]

# ALLOWED_ORIGIN_REGEX env var: a regex pattern for origins that can't be
# listed exactly - mainly Vercel PREVIEW deployments
allowed_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX") or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(history.router)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "ai-interview-coach-backend"}