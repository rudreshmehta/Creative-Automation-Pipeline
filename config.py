from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Vertex AI Configuration
    gcp_project_id: str = Field(...)
    gcp_location: str = Field(default="us-central1")

    # Gemini/Imagen Models
    imagen_model: str = Field(default="imagen-3.0-generate-002")
    gemini_text_model: str = Field(default="gemini-2.5-flash")
    gemini_api_key: str = Field(default="")  # Optional for text-only

    log_level: str = Field(default="INFO")
    max_retries: int = Field(default=3)
    timeout_seconds: int = Field(default=30)

    imagen_rpm_limit: int = Field(default=60)

    output_dir: Path = Field(default=Path("outputs"))
    reports_dir: Path = Field(default=Path("reports"))
    assets_dir: Path = Field(default=Path("assets"))

    # Dropbox Configuration
    dropbox_access_token: str = Field(default="")
    dropbox_upload_enabled: bool = Field(default=True)
    dropbox_base_path: str = Field(default="/creative-automation")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

settings.output_dir.mkdir(exist_ok=True)
settings.reports_dir.mkdir(exist_ok=True)
settings.assets_dir.mkdir(exist_ok=True)
(settings.assets_dir / "products").mkdir(exist_ok=True)
(settings.assets_dir / "brands").mkdir(exist_ok=True)
(settings.assets_dir / "fonts").mkdir(exist_ok=True)
