# scrape.py
import json
import os
from pages import SEED_PAGES
from fetch import fetch_with_rate_limit
from clean import extract_sections

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw")

def scrape_page(page_title):
    print(f"Scraping: {page_title}")
    
    wikitext = fetch_with_rate_limit(page_title)
    if not wikitext:
        return None
    
    sections = extract_sections(wikitext, page_title)
    # sections = filter_frlg_sections(sections)
    
    result = {
        "page_title": page_title,
        "source_url": f"https://bulbapedia.bulbagarden.net/wiki/{page_title.replace(' ', '_')}",
        "sections": sections
    }
    
    return result


def save_page(data, page_title):
    # Sanitize filename
    filename = page_title.replace(" ", "_").replace("/", "-") + ".json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved {len(data['sections'])} sections → {filename}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_pages = SEED_PAGES #add more than walkthroughs here if needed
    total = len(all_pages)
    
    for i, page_title in enumerate(all_pages):
        print(f"[{i+1}/{total}]", end=" ")
        
        # Skip if already scraped (resume support)
        filename = page_title.replace(" ", "_") + ".json"
        if os.path.exists(os.path.join(OUTPUT_DIR, filename)):
            print(f"Already scraped, skipping: {page_title}")
            continue
        
        data = scrape_page(page_title)
        if data:
            save_page(data, page_title)


if __name__ == "__main__":
    main()