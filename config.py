"""
Companion's config loader.

Reads credentials from a local `.env` file (never commit this file).
Create `.env` in the same folder as this file, based on `.env.example`.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
MS_TENANT_ID = os.getenv("MS_TENANT_ID", "common")  # "common" works for personal MS accounts