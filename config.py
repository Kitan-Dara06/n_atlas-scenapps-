import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Hugging Face Authentication
    hf_token: str

    # Model Configuration
    n_atlas_model: str = "NCAIR1/NigerianAccentedEnglish"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Storage
    temp_audio_dir: str = "./temp_audio"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    def get_temp_audio_path(self) -> Path:
        """Get Path object for temp audio directory"""
        path = Path(self.temp_audio_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()
