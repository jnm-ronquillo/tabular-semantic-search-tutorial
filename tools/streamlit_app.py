import requests
import streamlit as st

API_BASE = "http://localhost:8080"
QUERY_ENDPOINT = f"{API_BASE}/api/v1/search/product"

KICKSTART_QUERIES = [
    "Cheap but highly rated electronics under $50",
    "Best books about history with many reviews",
    "Affordable kitchen gadgets for meal prep",
    "Top rated pet supplies, popular items",
]


def make_query(query: str, limit: int = 3) -> dict | None:
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-include-metadata": "true",
    }
    payload = {"natural_query": query, "limit": limit}

    try:
        response = requests.post(QUERY_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error making request: {str(e)}")
        return None


def format_applied_filters(search_params: dict) -> str:
    """Format the NLQ-extracted search parameters for display."""
    skip_keys = {
        "similar_description_weight", "similar_title_weight",
        "limit", "radius", "natural_query",
        "title_weight", "description_weight",
    }
    lines = []
    for key, value in sorted(search_params.items()):
        if key in skip_keys or key.startswith("system_prompt") or key.startswith("select_param"):
            continue
        if value is None or value == "" or value == 0:
            continue
        lines.append(f"- **{key}**: `{value}`")
    return "\n".join(lines) if lines else "_No specific filters applied._"


def main():
    st.title("Search Amazon Products")
    st.markdown("**Tabular Semantic Search** powered by Superlinked and Qdrant")

    # Kick-start options
    st.markdown("**Try a query:**")
    cols = st.columns(len(KICKSTART_QUERIES))
    for i, q in enumerate(KICKSTART_QUERIES):
        if cols[i].button(q, key=f"kick_{i}"):
            st.session_state["query_input"] = q

    # Query input
    query_text = st.text_input(
        "Enter your search query:",
        value=st.session_state.get("query_input", ""),
        placeholder="e.g., cheap books with a rating bigger than 4",
    )

    # Number of results
    limit = st.slider("Number of results", min_value=1, max_value=10, value=3)

    if st.button("Search") or st.session_state.get("query_input"):
        if query_text:
            st.session_state.pop("query_input", None)
            with st.spinner("Searching..."):
                results = make_query(query_text, limit)

            if results and "entries" in results:
                # Display applied filters from NLQ extraction
                if "search_params" in results.get("metadata", {}):
                    with st.expander("Applied search parameters", expanded=False):
                        st.markdown(format_applied_filters(results["metadata"]["search_params"]))

                st.subheader(f"Results ({len(results['entries'])} found)")

                for item in results["entries"]:
                    fields = item.get("fields", {})
                    score = item.get("metadata", {}).get("score", "N/A")

                    with st.container():
                        st.markdown(f"""
#### {fields.get('title', 'N/A')}
- **Price:** ${fields.get('price', 'N/A')} | **Rating:** {fields.get('review_rating', 'N/A')}/5 ({fields.get('review_count', 'N/A')} reviews)
- **Type:** {fields.get('type', 'N/A')} | **Category:** {', '.join(fields.get('category', [])) if isinstance(fields.get('category'), list) else fields.get('category', 'N/A')}
- **Score:** {f"{float(score):.4f}" if score != "N/A" else "N/A"} | **ASIN:** {item.get('id', 'N/A')}
---
""")
            else:
                st.warning("No results found.")
        else:
            st.warning("Please enter a search query.")


if __name__ == "__main__":
    main()
