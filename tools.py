from langchain.agents import tool
from langchain_community.utilities import WikipediaAPIWrapper

@tool
def wikipedia_query(query: str) -> str:
    """
    Query Wikipedia and return a concise summary.
    Input: a search query string.
    """
    try:
        wiki_api = WikipediaAPIWrapper(
            lang="en",
            top_k_results=2,
            doc_content_chars_max=500,
        )
        return wiki_api.run(query)
    except Exception as e:
        return f"Error querying Wikipedia: {str(e)}"


tools = [wikipedia_query]