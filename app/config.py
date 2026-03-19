from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    upload_dir: Path = Field(default=Path("data/uploads"), env="UPLOAD_DIR")
    chroma_dir: Path = Field(default=Path("data/chroma_db"), env="CHROMA_DIR")
    max_upload_size_mb: int = Field(default=50, env="MAX_UPLOAD_SIZE_MB")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    claude_model: str = "claude-opus-4-6"

    model_config = {"env_file": ".env", "extra": "ignore"}

    def ensure_dirs(self) -> None:
        for d in [self.data_dir, self.upload_dir, self.chroma_dir,
                  self.data_dir / "assessments"]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
