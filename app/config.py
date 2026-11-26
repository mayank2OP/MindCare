"""
MindCare Configuration & Settings
Handles environment variables, default model selection, and storage paths.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "MindCare Signal"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Directories
    BASE_PATH: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "data" / "knowledge_base"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma_db"
    MODEL_PATH: Path = BASE_DIR / "Mental_Health_Model.pkl"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"

    # LLM API Keys & Provider configs
    # Providers supported: 'gemini', 'groq', 'ollama', 'offline'
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # RAG Settings
    LIGHTWEIGHT_RAG: bool = False
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_CHUNKS: int = 4

    # Model parameters
    TOP_COUNTRIES: list[str] = [
        "Other", "India", "USA", "Canada", "Australia",
        "UK", "Germany", "Mexico", "Turkey", "France"
    ]

    # JWT Authentication
    JWT_SECRET: str = "mindcare-dev-secret-change-in-production"
    JWT_EXPIRY_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
