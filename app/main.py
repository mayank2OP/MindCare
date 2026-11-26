"""
MindCare Signal — Production FastAPI Application
ML + SHAP + RAG + LLM + JWT Auth + Crisis Safety Guardrails.
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.auth.routes import router as auth_router
from app.auth.deps import get_current_user
from app.auth.models import User  # noqa: F401 — registers table with Base
from app.models.schemas import (
    StudentData, PredictionResponse, ExplainResponse,
    PlanRequest, PlanResponse, ChatRequest, ChatResponse,
)
from app.services import predictor, explainer_service, rag_engine, safety_guard, llm_service


# -------------------------------------------------------------------------
# Application lifecycle
# -------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print(f"🚀 Initializing {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  + Database: SQLite ready")
    print(f"  + ML Model: Loaded ({settings.MODEL_PATH.name})")
    print(f"  + SHAP Explainer: Ready (base score: {explainer_service.base_value:.2f})")
    print(f"  + RAG Vector Store: {rag_engine.collection.count()} chunks indexed")
    print(f"  + Safety Guardrail: Active")
    print(f"  + LLM Provider: {settings.LLM_PROVIDER}")
    print(f"  + Auth: JWT enabled")
    yield
    print("🛑 Shutting down MindCare Signal.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Student Mental Health Analytics with ML, SHAP, RAG, LLM, and JWT Auth.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# -------------------------------------------------------------------------
# Protected endpoints (require JWT)
# -------------------------------------------------------------------------
@app.post("/predict", response_model=PredictionResponse, tags=["ML"])
def predict_score(data: StudentData, _user: User = Depends(get_current_user)):
    try:
        return predictor.predict(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/explain", response_model=ExplainResponse, tags=["SHAP"])
def explain_prediction(data: StudentData, _user: User = Depends(get_current_user)):
    try:
        return explainer_service.explain(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-plan", response_model=PlanResponse, tags=["GenAI"])
def generate_wellness_plan(req: PlanRequest, _user: User = Depends(get_current_user)):
    try:
        explained = explainer_service.explain(req.student_data)
        chunks = rag_engine.retrieve_multi(explained.search_queries, top_k_per_query=2)
        return llm_service.generate_plan(
            score=explained.predicted_score,
            risk_factors=explained.risk_factors,
            protective_factors=explained.protective_factors,
            retrieved_sources=chunks,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat_assistant(req: ChatRequest, _user: User = Depends(get_current_user)):
    try:
        is_crisis, trigger = safety_guard.check_text(req.message)
        if is_crisis:
            alert = safety_guard.create_crisis_alert(trigger or "distress")
            return ChatResponse(
                reply=alert.message, sources=[], is_crisis=True,
                safety_alert=alert, medical_disclaimer=safety_guard.get_disclaimer(),
                provider_used="Safety Guardrail Engine",
            )
        sources = rag_engine.retrieve(req.message, top_k=settings.TOP_K_CHUNKS)
        return llm_service.chat(
            message=req.message, history=req.history,
            retrieved_sources=sources, student_context=req.student_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------------
# Public endpoints
# -------------------------------------------------------------------------
@app.get("/knowledge-base", tags=["Knowledge Base"])
def get_knowledge_base_info():
    doc_files = list(Path(settings.KNOWLEDGE_BASE_DIR).glob("*.txt"))
    return {
        "status": "ready",
        "total_documents": len(doc_files),
        "total_indexed_chunks": rag_engine.collection.count(),
        "categories": ["Sleep", "Stress", "Screen Time", "Study Habits", "Exercise"],
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ml_model_loaded": predictor.model is not None,
        "rag_chunks_indexed": rag_engine.collection.count(),
    }


# -------------------------------------------------------------------------
# Serve React SPA (production build)
# -------------------------------------------------------------------------
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="static")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    if FRONTEND_DIR.exists():
        candidate = (FRONTEND_DIR / full_path).resolve()
        if candidate.is_relative_to(FRONTEND_DIR.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIR / "index.html")
    return {"message": f"{settings.APP_NAME} API running — visit /docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
