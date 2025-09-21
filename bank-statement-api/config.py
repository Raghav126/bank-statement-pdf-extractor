"""
Configuration file for Bank Statement API
Contains all configuration settings and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import tempfile

# Load environment variables from .env file
load_dotenv()

class Config:
    """Main configuration class"""
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"
    
    # Mistral API Configuration
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MISTRAL_OCR_MODEL = os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")
    MISTRAL_CHAT_MODEL = os.getenv("MISTRAL_CHAT_MODEL", "pixtral-12b-latest")
    
    # File Processing Configuration
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB default
    ALLOWED_EXTENSIONS = [".pdf"]
    TEMP_DIR = os.getenv("TEMP_DIR", tempfile.gettempdir())
    OUTPUT_DIR = os.getenv("OUTPUT_DIR")
    
    # Rate Limiting Configuration
    API_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", 1.0))  # seconds
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Validation
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        if not cls.MISTRAL_API_KEY:
            raise ValueError(
                "MISTRAL_API_KEY is required. Set it as an environment variable or in .env file"
            )
        
        # Create temp directory if it doesn't exist
        Path(cls.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_summary(cls):
        """Get configuration summary for debugging"""
        return {
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "debug_mode": cls.API_DEBUG,
            "max_file_size_mb": cls.MAX_FILE_SIZE / (1024 * 1024),
            "temp_dir": cls.TEMP_DIR,
            "mistral_models": {
                "ocr": cls.MISTRAL_OCR_MODEL,
                "chat": cls.MISTRAL_CHAT_MODEL
            },
            "rate_limit_delay": cls.API_RATE_LIMIT_DELAY,
            "cors_origins": cls.CORS_ORIGINS
        }

# Validate configuration on import
Config.validate_config()