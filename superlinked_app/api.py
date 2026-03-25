import superlinked.framework as sl
from loguru import logger
from superlinked.framework.dsl.executor.interactive.interactive_executor import (
    InteractiveExecutor,
)
from superlinked.framework.dsl.source.in_memory_source import InMemorySource

from superlinked_app import index, query
from superlinked_app.config import settings

# In-memory data source (for programmatic ingestion, no HTTP server needed)
product_source = InMemorySource(index.product)

# Qdrant vector database
vector_database = sl.QdrantVectorDatabase(
    settings.QDRANT_URL,
    settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None,
)

# Interactive executor with Qdrant backend — uses the open-source SDK directly
executor = InteractiveExecutor(
    sources=[product_source],
    indices=[index.product_index],
    vector_database=vector_database,
)

# The app is created when .run() is called — done in server.py at startup
app = None


def start():
    """Initialize the superlinked app. Call once at startup."""
    global app
    logger.info("Starting superlinked InMemoryExecutor...")
    app = executor.run()
    logger.info("Superlinked app ready.")
    return app


def load_data() -> None:
    """Load the product dataset into the index via the in-memory source."""
    import pandas as pd

    if app is None:
        raise RuntimeError("App not started. Call start() first.")

    path = settings.PROCESSED_DATASET_PATH
    settings.validate_processed_dataset_exists()
    logger.info(f"Loading data from: {path}")

    for chunk in pd.read_json(path, lines=True, chunksize=settings.chunk_size):
        records = chunk.rename(columns={"asin": "id"}).to_dict(orient="records")
        product_source.put(records)

    logger.info("Data loading complete.")
