from pathlib import Path

from loguru import logger
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"
logger.info(f"Loading '.env' file from: {ENV_FILE}")

assert ENV_FILE.exists(), ".env doesn't exists at the expected location"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    # Embeddings
    text_embedder_name: str = "sentence-transformers/all-mpnet-base-v2"
    chunk_size: int = 100

    # Superlinked
    PROCESSED_DATASET_PATH: Path = (
        Path("data") / "processed_300_sample.jsonl"
    )  # or change it for a bigger dataset to: processed_850_sample.jsonl
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: SecretStr | None = None

    # Vertex AI / Gemini (via OpenAI-compatible API)
    VERTEX_MODEL_ID: str = "google/gemini-2.5-flash"
    VERTEX_LOCATION: str = "europe-southwest1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    @model_validator(mode="after")
    def validate_qdrant_config(self) -> "Settings":
        """Validates that Qdrant URL is configured."""
        if not self.QDRANT_URL:
            raise ValueError("QDRANT_URL is required.")
        return self

    def validate_processed_dataset_exists(self):
        if not self.PROCESSED_DATASET_PATH.exists():
            raise ValueError(
                f"Processed dataset not found at '{self.PROCESSED_DATASET_PATH}'. "
                "Please run 'make download-and-process-sample-dataset' first to download and process the Amazon dataset."
            )


settings = Settings()
