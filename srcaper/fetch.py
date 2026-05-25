import requests
import time

BASE_URL = "https://bulbapedia.bulbagarden.net/w/api.php"

HEADERS = {
    "User-Agent": "FRLGRagBot/1.0 (personal learning project; not for redistribution)"
}


def fetch_page_html(page_title):
    """
    Fetch the fully rendered HTML for a page via the MediaWiki parse API.
    Returns an HTML string or None if the page is not found.

    Using action=parse instead of action=query+revisions because it returns
    rendered HTML with all templates already expanded — no need to parse
    wikitext or handle template edge cases manually.
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "format": "json",
        "formatversion": "2",
    }

    response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        print(f"  [SKIP] Page not found: {page_title}")
        return None

    return data["parse"]["text"]


def fetch_with_rate_limit(page_title, delay=1.5):
    """Enforce a polite delay between requests."""
    result = fetch_page_html(page_title)
    time.sleep(delay)
    return result