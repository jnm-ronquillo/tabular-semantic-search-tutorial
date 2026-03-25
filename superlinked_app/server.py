"""
Custom FastAPI server replacing superlinked-server.

Uses the open-source superlinked SDK (InMemoryExecutor) directly,
giving full control over API endpoints, middleware, auth, etc.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from superlinked_app import api, query


# --- Request/Response models ---


class SearchRequest(BaseModel):
    natural_query: str
    limit: int = Field(default=3, ge=1, le=100)


class SimilarItemsRequest(BaseModel):
    natural_query: str
    product_id: str
    limit: int = Field(default=3, ge=1, le=100)


class DebugRequest(BaseModel):
    limit: int = Field(default=3, ge=1, le=100)


# --- App lifecycle ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    api.start()
    yield


app = FastAPI(title="Product Semantic Search", lifespan=lifespan)


# --- Endpoints ---


@app.post("/api/v1/search/product")
def search_product(req: SearchRequest):
    """Multi-modal semantic search with NLQ parameter extraction."""
    if api.app is None:
        raise HTTPException(status_code=503, detail="App not initialized")

    result = api.app.query(
        query.query,
        natural_query=req.natural_query,
        limit=req.limit,
    )
    return _format_result(result)


@app.post("/api/v1/search/product-debug")
def search_product_debug(req: DebugRequest | None = None):
    """Debug query to check if data is ingested."""
    if api.app is None:
        raise HTTPException(status_code=503, detail="App not initialized")

    limit = req.limit if req else 3
    result = api.app.query(query.query_debug, limit=limit)
    return _format_result(result)


@app.post("/api/v1/search/similar_items")
def search_similar_items(req: SimilarItemsRequest):
    """Find products similar to a given product."""
    if api.app is None:
        raise HTTPException(status_code=503, detail="App not initialized")

    result = api.app.query(
        query.similar_items_query,
        natural_query=req.natural_query,
        product_id=req.product_id,
        limit=req.limit,
    )
    return _format_result(result)


@app.post("/data-loader/product/run")
def load_data():
    """Trigger batch data loading from the processed dataset."""
    try:
        api.load_data()
        return {"status": "ok", "message": "Data loaded successfully"}
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Helpers ---


def _format_result(result) -> dict:
    """Convert superlinked QueryResult to the same JSON shape the Streamlit app expects."""
    entries = []
    for item in result.entries:
        entry = {
            "id": item.id,
            "fields": item.fields,
            "metadata": {"score": item.metadata.score},
        }
        entries.append(entry)

    response: dict = {"entries": entries}

    # Include search metadata if available (NLQ-extracted params)
    if result.metadata and result.metadata.search_params:
        response["metadata"] = {"search_params": result.metadata.search_params}

    return response
