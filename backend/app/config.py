import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes"}


def model_name() -> str:
    return os.getenv("META_MODEL", "muse-spark-1.3")


def model_base_url() -> str:
    return os.getenv("META_BASE_URL", "https://api.meta.ai/v1")
