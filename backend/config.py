"""
Application settings — loaded from .env / environment variables.
All inference configuration lives here so nothing is hardcoded.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional
from enum import Enum
from functools import lru_cache


class InferenceBackend(str, Enum):
    OLLAMA = "ollama"
    VLLM = "vllm"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Inference backend ──────────────────────────────────────────────────
    inference_backend: InferenceBackend = InferenceBackend.OLLAMA

    # ── Ollama ─────────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_models: str = "llama3,mistral"  # CSV → list via property

    # ── vLLM ───────────────────────────────────────────────────────────────
    vllm_base_url: str = "http://localhost:8001"
    vllm_models: Optional[str] = None

    # ── Cloud ──────────────────────────────────────────────────────────────
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # ── Evaluation ─────────────────────────────────────────────────────────
    default_num_variants: int = 5
    default_max_tokens: int = 512
    default_temperature: float = 0.0
    inference_concurrency: int = 4

    # ── Storage ────────────────────────────────────────────────────────────
    db_path: str = "./data/results.duckdb"

    # ── API server ─────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # ── Properties ─────────────────────────────────────────────────────────
    @property
    def ollama_model_list(self) -> List[str]:
        return [m.strip() for m in self.ollama_models.split(",") if m.strip()]

    @property
    def vllm_model_list(self) -> List[str]:
        if not self.vllm_models:
            return []
        return [m.strip() for m in self.vllm_models.split(",") if m.strip()]

    @property
    def all_local_models(self) -> List[str]:
        models = self.ollama_model_list[:]
        models += self.vllm_model_list
        return models

    def model_provider(self, model_id: str) -> InferenceBackend:
        """Determine which backend handles a given model id."""
        if model_id in self.vllm_model_list:
            return InferenceBackend.VLLM
        if model_id in self.ollama_model_list or "/" not in model_id:
            return InferenceBackend.OLLAMA
        if model_id.startswith("gpt"):
            return InferenceBackend.OPENAI
        if model_id.startswith("claude"):
            return InferenceBackend.ANTHROPIC
        return self.inference_backend  # default from env


@lru_cache
def get_settings() -> Settings:
    return Settings()
