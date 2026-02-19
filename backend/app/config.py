"""
Application configuration loaded from environment variables.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from backend root
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)


class Settings(BaseSettings):
    """App settings from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./ticketing.db"

    # Algorand
    algod_server: str = "https://testnet-api.algonode.cloud"
    algod_token: str = ""
    indexer_server: str = "https://testnet-idx.algonode.cloud"
    indexer_token: str = ""

    # App
    app_id: int = 0
    deployer_mnemonic: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields like VITE_APP_ID


settings = Settings()
