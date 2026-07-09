from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import session, history

app = FastAPI(title="AI Interview Coach", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(session.router)
app.include_router(history.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "ai-interview-coach-backend"}
