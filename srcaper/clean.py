import re
from bs4 import BeautifulSoup


# CSS classes to strip entirely before processing — pure visual/nav noise
GARBAGE_CLASSES = {
    "thumb", "thumbinner", "thumbcaption",  # image thumbnails
    "navbox", "navbox-inner",               # navigation boxes at page bottom
    "toc",                                  # table of contents
    "mw-editsection",                       # [edit] links next to headings
    "printfooter", "catlinks",              # page footer
    "infobox",                              # sidebar infoboxes
}

OTHER_GAME_KEYWORDS = [
    "Generation II", "Gold and Silver", "HeartGold", "SoulSilver",
    "Diamond and Pearl", "Platinum", "Black and White", "Black 2 and White 2",
    "X and Y", "Omega Ruby", "Alpha Sapphire", "Sun and Moon",
    "Ultra Sun", "Ultra Moon", "Sword and Shield", "Scarlet and Violet",
    "Brilliant Diamond", "Legends: Arceus",
]


def strip_noise(soup):
    """Remove elements that only add visual noise to the extracted text."""
    for cls in GARBAGE_CLASSES:
        for el in soup.find_all(class_=cls):
            el.decompose()
    return soup


def table_to_text(table):
    """
    Convert a rendered HTML table into readable plain-text sentences.

    Detects the table's header row (th elements) and uses it as a label
    prefix, then joins each data row's cells with commas.

    Example output:
      "Trainers: Bug Catcher Rick, Reward: $72. Weedle Lv.6, Caterpie Lv.6."
      "Available Pokémon: Pikachu, FR LG, 3-5, 5%."
      "Items: Poké Ball, Northwest grassy path."
    """
    rows = table.find_all("tr")
    if not rows:
        return ""

    # Detect header label from first row's th element
    header_text = ""
    first_ths = rows[0].find_all("th")
    if first_ths:
        header_text = first_ths[0].get_text(" ", strip=True)

    parts = []
    for row in rows:
        # Skip pure header rows (all th, no td)
        tds = row.find_all("td")
        ths = row.find_all("th")
        if ths and not tds:
            continue

        cells = [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]
        cells = [c for c in cells if c and c != header_text]
        if not cells:
            continue

        parts.append(", ".join(cells))

    if not parts:
        return ""

    prefix = f"{header_text}: " if header_text else ""
    return prefix + ". ".join(parts) + "."


def extract_sections(html, page_title):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", class_="mw-parser-output")
    if not content:
        return []
    content = strip_noise(content)

    sections = []
    current_heading = page_title
    prose_parts = []

    def flush_prose():
        if prose_parts:
            text = clean_text(" ".join(prose_parts))
            if len(text) > 50:
                sections.append({
                    "heading": current_heading,
                    "text": text,
                })
            prose_parts.clear()

    for element in content.children:
        tag = getattr(element, "name", None)
        if tag is None:
            continue

        if tag in ("h2", "h3", "h4"):
            flush_prose()
            heading = element.get_text(" ", strip=True)
            current_heading = re.sub(r'\[edit\]', '', heading).strip()

        elif tag == "p":
            text = element.get_text(" ", strip=True)
            if text:
                prose_parts.append(text)

        elif tag == "table":
            # Each table becomes its own chunk
            text = table_to_text(element)
            if text:
                flush_prose()
                sections.append({
                    "heading": current_heading,
                    "text": clean_text(text),
                })

        elif tag == "div":
            # Only find direct child tables to avoid double-processing
            for tbl in element.find_all("table", recursive=False):
                text = table_to_text(tbl)
                if text:
                    flush_prose()
                    sections.append({
                        "heading": current_heading,
                        "text": clean_text(text),
                    })

    flush_prose()
    return sections

def encounter_table_to_text(table):
    """
    Convert Available Pokémon tables into natural language sentences
    instead of raw cell dumps.
    
    "Pikachu FR LG Grass 3, 5 5%"
    →
    "Pikachu can be found in Grass at levels 3, 5 (5% encounter rate)."
    """
    rows = table.find_all("tr")
    if not rows:
        return ""

    # Detect if this is a Pokémon encounter table by checking headers
    headers = [th.get_text(" ", strip=True).lower() for th in rows[0].find_all("th")]
    is_encounter_table = "rate" in headers and "levels" in headers

    if not is_encounter_table:
        return table_to_text(table)   # fall back to generic for trainer/item tables

    # Find column positions from headers
    try:
        pokemon_col  = next(i for i, h in enumerate(headers) if "pokémon" in h or "pokemon" in h)
        location_col = next(i for i, h in enumerate(headers) if "location" in h)
        levels_col   = next(i for i, h in enumerate(headers) if "level" in h)
        rate_col     = next(i for i, h in enumerate(headers) if "rate" in h)
    except StopIteration:
        return table_to_text(table)   # headers didn't match expected, fall back

    sentences = []
    seen = set()

    for row in rows[1:]:   # skip header row
        cells = [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]
        cells = [c for c in cells if c]

        if len(cells) <= max(pokemon_col, location_col, levels_col, rate_col):
            continue

        pokemon  = cells[pokemon_col]
        location = cells[location_col]
        levels   = cells[levels_col]
        rate     = cells[rate_col]

        # Deduplicate — Bulbapedia renders image+text in same cell
        # causing "Pikachu Pikachu" — take first word-group only
        pokemon = dedupe_cell(pokemon)

        key = (pokemon, levels, rate)
        if key in seen:
            continue
        seen.add(key)

        sentences.append(
            f"{pokemon} can be found in {location} at level {levels} ({rate} encounter rate)."
        )

    if not sentences:
        return ""

    return "Available Pokémon: " + " ".join(sentences)


def dedupe_cell(text):
    """'Pikachu Pikachu' → 'Pikachu',  'FR LG FR LG' → 'FR LG'"""
    words = text.split()
    half = len(words) // 2
    if half > 0 and words[:half] == words[half:]:
        return " ".join(words[:half])
    return text

def filter_frlg_sections(sections):
    """Drop sections whose headings clearly reference other game generations."""
    filtered = []
    for section in sections:
        if any(kw.lower() in section["heading"].lower() for kw in OTHER_GAME_KEYWORDS):
            continue
        filtered.append(section)
    return filtered


def clean_text(text):
    """Remove citation markers, edit links, and collapse whitespace."""
    text = re.sub(r'\[\d+\]', '', text)   # [1] [2] citation markers
    text = re.sub(r'\[edit\]', '', text)   # [edit] section links
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()