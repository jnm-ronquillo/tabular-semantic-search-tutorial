import superlinked.framework as sl
from loguru import logger

from superlinked_app import index, query
from superlinked_app.config import settings

# Real-time data source (takes items one by one through HTTP requests)
product_source = sl.RestSource(index.product)

# Batch data loader (loads static dataset)
logger.info(f"Data loader will load data from: '{settings.PROCESSED_DATASET_PATH}'")
settings.validate_processed_dataset_exists()
product_data_loader_parser = sl.DataFrameParser(
    schema=index.product, mapping={index.product.id: "asin"}
)
product_data_loader_config = sl.DataLoaderConfig(
    str(settings.PROCESSED_DATASET_PATH),
    sl.DataFormat.JSON,
    pandas_read_kwargs={"lines": True, "chunksize": settings.chunk_size},
)
product_loader_source = sl.DataLoaderSource(
    index.product,
    data_loader_config=product_data_loader_config,
    parser=product_data_loader_parser,
)

# Qdrant vector database
vector_database = sl.QdrantVectorDatabase(
    settings.QDRANT_URL,
    settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None,
)

# REST executor with all queries
executor = sl.RestExecutor(
    sources=[product_source, product_loader_source],
    indices=[index.product_index],
    queries=[
        sl.RestQuery(sl.RestDescriptor("product"), query.query),
        sl.RestQuery(sl.RestDescriptor("product-debug"), query.query_debug),
        sl.RestQuery(sl.RestDescriptor("similar_items"), query.similar_items_query),
    ],
    vector_database=vector_database,
)

sl.SuperlinkedRegistry.register(executor)
