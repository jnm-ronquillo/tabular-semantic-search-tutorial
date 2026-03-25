from superlinked import framework as sl

from superlinked_app.config import settings


class Product(sl.Schema):
    # `id` is obligatory
    id: sl.IdField
    #
    # fields embedded into spaces for semantic search
    title: sl.String
    description: sl.String
    review_rating: sl.Float
    review_count: sl.Integer
    price: sl.Float
    #
    # fields used only for hard-filtering
    type: sl.String
    category: sl.StringList


product = Product()

# title and description are embedded using sentence-transformer model
title_space = sl.TextSimilaritySpace(
    text=product.title,
    model=settings.text_embedder_name,
)
description_space = sl.TextSimilaritySpace(
    text=product.description,
    model=settings.text_embedder_name,
)

# rating is embedded using linear scale
review_rating_space = sl.NumberSpace(
    product.review_rating,
    min_value=-1.0,
    max_value=5.0,
    mode=sl.Mode.MAXIMUM,
)

# price and review_count are embedded using logarithmic scale
# because their distributions span multiple orders of magnitude
price_space = sl.NumberSpace(
    product.price,
    min_value=0.0,
    max_value=1000,
    mode=sl.Mode.MAXIMUM,
    scale=sl.LogarithmicScale(),
)

review_count_space = sl.NumberSpace(
    product.review_count,
    min_value=0,
    max_value=10000,
    mode=sl.Mode.MAXIMUM,
    scale=sl.LogarithmicScale(),
)

# index is a composition of spaces
product_index = sl.Index(
    spaces=[
        title_space,
        description_space,
        review_rating_space,
        price_space,
        review_count_space,
    ],
    # fields below are used for hard-filtering
    fields=[
        product.type,
        product.category,
        product.review_rating,
        product.review_count,
        product.price,
    ],
)
