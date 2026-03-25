from collections import namedtuple

from superlinked import framework as sl

from superlinked_app import constants
from superlinked_app.index import (
    description_space,
    price_space,
    product,
    product_index,
    review_count_space,
    review_rating_space,
    title_space,
)
from superlinked_app.nlq import (
    description_description,
    gemini_config,
    price_description,
    review_count_description,
    review_rating_description,
    system_prompt,
    title_description,
)

# Debug query to check if server has data ingested
query_debug = sl.Query(product_index).find(product).limit(3).select_all()

# Main query for multi-modal semantic search
query = (
    sl.Query(
        product_index,
        weights={
            title_space: sl.Param("title_weight", default=1.0),
            description_space: sl.Param("description_weight", default=1.0),
            review_rating_space: sl.Param(
                "review_rating_weight",
                description=review_rating_description,
            ),
            price_space: sl.Param(
                "price_weight",
                description=price_description,
            ),
            review_count_space: sl.Param(
                "review_count_weight",
                description=review_count_description,
            ),
        },
    )
    .find(product)
    .similar(
        description_space.text,
        sl.Param("query_description", description=description_description),
        weight=sl.Param("similar_description_weight", default=1.0),
    )
    .similar(
        title_space.text,
        sl.Param("query_title", description=title_description),
        weight=sl.Param("similar_title_weight", default=1.0),
    )
)

# Result limit and metadata
query = query.limit(sl.Param("limit", default=3))
query = query.select_all()
query = query.include_metadata()

# Hard filters: product type
query = query.filter(
    product.type
    == sl.Param(
        "filter_by_type",
        description="Used to only present items of a specific type.",
        options=constants.TYPES,
    )
)

# Hard filters: numeric ranges
query = (
    query.filter(
        product.review_rating
        >= sl.Param(
            "min_review_rating",
            description="Minimum review rating (0-5 scale).",
        )
    )
    .filter(
        product.review_rating
        <= sl.Param(
            "max_review_rating",
            description="Maximum review rating (0-5 scale).",
        )
    )
    .filter(
        product.price
        >= sl.Param(
            "min_price",
            description="Minimum price in USD.",
        )
    )
    .filter(
        product.price
        <= sl.Param(
            "max_price",
            description="Maximum price in USD.",
        )
    )
)

# Hard filters: categorical attributes using CategoryFilter pattern
CategoryFilter = namedtuple(
    "CategoryFilter", ["operator", "param_name", "category_name", "description"]
)

filters = [
    CategoryFilter(
        operator=product.category.contains_all,
        param_name="category_include_all",
        category_name="category",
        description="User wants products in ALL of the following categories.",
    ),
    CategoryFilter(
        operator=product.category.contains,
        param_name="category_include_any",
        category_name="category",
        description="User wants products in at least one of the following categories.",
    ),
    CategoryFilter(
        operator=product.category.not_contains,
        param_name="category_exclude",
        category_name="category",
        description="User does not want products in any of the following categories.",
    ),
]

for filter_item in filters:
    param = sl.Param(
        filter_item.param_name,
        description=filter_item.description,
        options=constants.CATEGORIES,
    )
    query = query.filter(filter_item.operator(param))

# Natural language interface on top: calls LLM to parse
# user query into structured superlinked query parameters
query = query.with_natural_query(
    natural_query=sl.Param("natural_query"),
    client_config=gemini_config,
    system_prompt=system_prompt,
)

# Similar items query: find products similar to a given product
similar_items_query = query.with_vector(product, sl.Param("product_id"))
