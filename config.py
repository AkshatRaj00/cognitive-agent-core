import os
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = os.getenv("MYTHOS_APP_TITLE", "Mythos 2.0 - Sovereign Defense Core")
SQLITE_PATH = os.getenv("MYTHOS_DB_PATH", "mythos_memory.db")
AUDIT_LOG_PATH = os.getenv("MYTHOS_AUDIT_LOG_PATH", "mythos_audit.jsonl")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_ENABLE_WEB_SEARCH = os.getenv("OPENAI_ENABLE_WEB_SEARCH", "false").lower() == "true"

ALLOW_DOCKER = os.getenv("MYTHOS_ALLOW_DOCKER", "false").lower() == "true"
DOCKER_TARGET_CONTAINER = os.getenv("MYTHOS_DOCKER_TARGET", "").strip()

DEFAULT_FEEDS = [
    "https://raw.githubusercontent.com/AkshatRaj00/OneMusic/main/README.md"
]
