import os
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = os.getenv("MYTHOS_APP_TITLE", "Mythos 2.0 - Sovereign Defense Core")
SQLITE_PATH = os.getenv("MYTHOS_DB_PATH", "mythos_memory.db")
AUDIT_LOG_PATH = os.getenv("MYTHOS_AUDIT_LOG_PATH", "mythos_audit.jsonl")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").strip()

ALLOW_DOCKER = os.getenv("MYTHOS_ALLOW_DOCKER", "false").lower() == "true"
DOCKER_TARGET_CONTAINER = os.getenv("MYTHOS_DOCKER_TARGET", "").strip()

DEFAULT_FEEDS = [
    "https://raw.githubusercontent.com/AkshatRaj00/OneMusic/main/README.md"
]

TRUSTED_HINTS = [
    "githubusercontent.com",
    "github.com",
    "cve",
    "security",
    "advisory",
    "nvd",
    "exploit",
    "blog",
]
