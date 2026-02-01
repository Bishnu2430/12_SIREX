"""
FastAPI Configuration Settings
Loads all environment variables and configures application settings
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
from loguru import logger

# Load .env file - try multiple locations
# 1. Current working directory
# 2. Parent of parent of this file (project root)
env_locations = [
    Path.cwd() / '.env',
    Path(__file__).parent.parent / '.env',
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    # Try to find .env by walking up directories
    search_dir = Path.cwd()
    for _ in range(5):  # Search up to 5 levels
        env_file = search_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            env_loaded = True
            break
        search_dir = search_dir.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Directories
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "storage" / "outputs"
    CACHE_DIR: Path = BASE_DIR / "storage" / "cache"
    LOG_DIR: Path = BASE_DIR / "storage" / "logs"
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 500
    
    # Google API Configuration
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""  # Alias for GEMINI_API_KEY
    GEMINI_MODEL: str = "gemini-2.5-flash-latest"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # GitHub API Configuration
    GITHUB_ACCESS_TOKEN: str = ""
    
    # Twitter API Configuration
    TWITTER_BEARER_TOKEN: str = ""
    
    # IP OSINT Configuration (optional)
    ABUSEIPDB_API_KEY: str = ""  # Optional: for threat intelligence
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_ENABLED: bool = True
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "osint"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_ENABLED: bool = False
    
    # Feature Flags
    USE_GOOGLE_VISION: bool = True
    USE_GPU: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set GOOGLE_API_KEY from GEMINI_API_KEY if not set
        if not self.GOOGLE_API_KEY and self.GEMINI_API_KEY:
            self.GOOGLE_API_KEY = self.GEMINI_API_KEY
        
        # Ensure directories exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def google_vision_enabled(self) -> bool:
        """Check if Google Vision API is properly configured"""
        if not self.USE_GOOGLE_VISION:
            return False
        
        # Check if credentials file exists
        if self.GOOGLE_APPLICATION_CREDENTIALS:
            creds_path = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
            return creds_path.exists()
        
        return False


# Initialize settings
settings = Settings()

# Set environment variable for Google Cloud if configured
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

# Set Gemini API key environment variable
if settings.GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
    logger.info(f"✓ Set GOOGLE_API_KEY from GEMINI_API_KEY (prefix: {settings.GEMINI_API_KEY[:20]}...)")
elif settings.GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
    logger.info(f"✓ Set GOOGLE_API_KEY directly (prefix: {settings.GOOGLE_API_KEY[:20]}...)")
else:
    logger.warning("⚠ No GEMINI_API_KEY or GOOGLE_API_KEY found in .env file")
