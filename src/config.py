from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field, validator

from .utils.file_manager import ensure_dirs


class Config(BaseModel):
    """
    Runtime configuration loaded from config.json with environment overrides.

    Fields:
      - api_key: API key for the model provider (only used with openai backend).
      - api_base: Base URL for API (only used with openai backend).
      - model: Model identifier.
      - max_concurrent: Maximum concurrent requests.
      - rate_limit_per_min: Rate limit per minute for requests.
      - cache_enabled: Whether response caching is enabled.
      - cache_dir: Directory path for cache files.
      - data_dir: Directory path for data files.
      - outputs_dir: Directory path for output artifacts.
      - templates_dir: Directory path for templates.
      - request_timeout_seconds: HTTP request timeout.
      - retry_attempts: Number of retry attempts on transient errors.
      - retry_backoff_seconds: Initial backoff in seconds (exponential).
    """

    # API fields - only used when backend="openai"
    api_key: Optional[str] = Field(default=None)
    api_base: Optional[str] = Field(default="https://api.openai.com/v1")
    
    # Core fields
    model: str = Field(default="gpt-oss-20b")
    max_concurrent: int = Field(default=5)
    rate_limit_per_min: int = Field(default=100)
    cache_enabled: bool = Field(default=True)
    cache_dir: str = Field(default="outputs/cache")
    data_dir: str = Field(default="data")
    outputs_dir: str = Field(default="outputs")
    templates_dir: str = Field(default="src/templates")
    request_timeout_seconds: int = Field(default=60)
    retry_attempts: int = Field(default=3)
    retry_backoff_seconds: float = Field(default=1.0)
    
    # Backend selection and HF generation defaults
    backend: str = Field(default="hf_local")
    hf_max_new_tokens: int = Field(default=256)
    hf_do_sample: bool = Field(default=True)
    hf_top_p: float = Field(default=0.95)
    hf_temperature: float = Field(default=0.7)
    # Optional 4-bit quantization and Hugging Face options
    hf_load_in_4bit: bool = Field(default=False)
    hf_bnb_4bit_quant_type: str = Field(default="nf4")
    hf_bnb_4bit_use_double_quant: bool = Field(default=True)
    hf_bnb_4bit_compute_dtype: str = Field(default="float16")  # or 'bfloat16'
    hf_max_memory: Optional[dict] = Field(default=None)
    hf_token: Optional[str] = Field(default=None)

    @validator("max_concurrent")
    def _validate_concurrency(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_concurrent must be > 0")
        return v

    @validator("rate_limit_per_min")
    def _validate_rate(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("rate_limit_per_min must be > 0")
        return v

    def effective_api_key(self) -> Optional[str]:
        """
        Return api_key, allowing environment variable OPENAI_API_KEY to override.
        """
        return os.getenv("OPENAI_API_KEY", self.api_key)

    def ensure_runtime_dirs(self) -> None:
        """
        Ensure required runtime directories exist (outputs and subdirs).
        """
        ensure_dirs(outputs_dir=self.outputs_dir)


def load_config(path: Optional[str] = "config.json") -> Config:
    """
    Load configuration from JSON file at 'path' if provided, else defaults.
    Apply environment variable override for OPENAI_API_KEY.
    Ensure directories exist.
    """
    import json

    defaults = {
        "api_key": None,
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-oss-20b",
        "backend": "hf_local",
        "max_concurrent": 5,
        "rate_limit_per_min": 100,
        "cache_enabled": True,
        "cache_dir": "outputs/cache",
        "data_dir": "data",
        "outputs_dir": "outputs",
        "templates_dir": "src/templates",
        "request_timeout_seconds": 60,
        "retry_attempts": 3,
        "retry_backoff_seconds": 1.0,
        "hf_max_new_tokens": 256,
        "hf_do_sample": True,
        "hf_top_p": 0.95,
        "hf_temperature": 0.7,
        "hf_load_in_4bit": False,
        "hf_bnb_4bit_quant_type": "nf4",
        "hf_bnb_4bit_use_double_quant": True,
        "hf_bnb_4bit_compute_dtype": "float16",
        "hf_max_memory": None,
        "hf_token": None,
    }

    data = defaults
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                cfg_json = json.load(f)
                if isinstance(cfg_json, dict):
                    data.update(cfg_json)
            except Exception as e:
                # Fall back to defaults if JSON is invalid
                print(f"[config] Failed to parse {path}: {e}. Using defaults.")

    cfg = Config(**data)
    # env override for api key
    key = os.getenv("OPENAI_API_KEY")
    if key:
        cfg.api_key = key

    # ensure directories
    cfg.ensure_runtime_dirs()

    return cfg


__all__ = ["Config", "load_config"]
