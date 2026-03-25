import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account
from superlinked import framework as sl

from superlinked_app.config import ROOT_DIR, settings

VERTEX_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


def _get_vertex_credentials():
    """Get OAuth2 credentials from the service account file."""
    creds_path = ROOT_DIR / settings.GOOGLE_APPLICATION_CREDENTIALS
    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path),
        scopes=VERTEX_SCOPES,
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials


_credentials = _get_vertex_credentials()

vertex_base_url = (
    f"https://{settings.VERTEX_LOCATION}-aiplatform.googleapis.com/v1beta1/"
    f"projects/{_credentials.project_id}/locations/{settings.VERTEX_LOCATION}/"
    f"endpoints/openapi/"
)

gemini_config = sl.OpenAIClientConfig(
    api_key=_credentials.token,
    model=settings.VERTEX_MODEL_ID,
    base_url=vertex_base_url,
    project=_credentials.project_id,
)

# --- NLQ Parameter Descriptions ---

description_description = (
    "'description' should be one or two normalized sentences that describe the desired product.\n"
    "Don't include price, rating, and review count mentions in the 'description'.\n"
    "Some examples of what should be captured in 'description': "
    "durable material, lightweight, easy to assemble, compact design, energy efficient.\n"
    "In case all requirements are captured by other parameters (type, category, etc.), "
    "description should be empty.\n"
    "Examples of 'description' generation:\n"
    "1. user_query: 'lightweight running shoes under $50 with great reviews' "
    "-> description: 'Lightweight running shoes.'\n"
    "2. user_query: 'affordable kitchen gadgets for meal prep' "
    "-> description: 'Kitchen gadgets suitable for meal preparation.'\n"
    "3. user_query: 'cheap books about history' "
    "-> description: ''\n"
)

title_description = (
    "'title' should capture the product name or type the user is looking for.\n"
    "Extract the core product identity from the query.\n"
    "Don't include price, rating, or category mentions.\n"
    "Examples:\n"
    "1. user_query: 'cheap wireless headphones with good reviews' -> title: 'wireless headphones'\n"
    "2. user_query: 'stainless steel water bottle under $20' -> title: 'stainless steel water bottle'\n"
)

price_description = (
    "Weight of the price. "
    "Higher value means more expensive products, "
    "lower value means cheaper ones. "
    "Weight depends on the adjective or noun used to describe the price. "
    "For example: "
    "positive weight: 'expensive', 'premium', 'high-end', 'luxury'; "
    "negative weight: 'cheap', 'affordable', 'budget', 'low price', 'cheapest'; "
    "0 should be used if no preference for the price."
)

review_rating_description = (
    "Weight of the review rating. "
    "Higher value means higher rated products, "
    "lower value means lower rated products. "
    "For example: "
    "positive weight: 'highly rated', 'best reviewed', 'top rated', 'good reviews'; "
    "negative weight: 'poorly rated', 'low rating'; "
    "0 should be used if no preference for the rating."
)

review_count_description = (
    "Weight of the review count. "
    "Higher value means more reviews (more popular), "
    "lower value means fewer reviews. "
    "For example: "
    "positive weight: 'popular', 'many reviews', 'best seller'; "
    "negative weight: 'few reviews', 'not popular'; "
    "0 should be used if no preference for the review count."
)

system_prompt = (
    "Extract the search parameters from the user query.\n"
    "Advices:\n"
    "**'type' filter**\n"
    "If the user searches for books, use type='book'. "
    "For all other products, use type='product'. "
    "If unclear, use None.\n"
    "**'category' filters**\n"
    "Use relevant categories from the available options. "
    "For example, 'kitchen gadgets' -> 'Kitchen & Dining' or 'Home & Kitchen'.\n"
    "If no specific category is mentioned, use None.\n"
)
