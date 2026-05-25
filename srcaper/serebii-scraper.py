import requests
import time
import json
import os
from bs4 import BeautifulSoup
from pages import SEREBII_ROUTE_URLS, SEREBII_POKEMON_URLS

HEADERS = {
    "User-Agent": "FRLGRagBot/1.0 (personal learning project; not for redistribution)"
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def fetch(url, delay=1.5):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    time.sleep(delay)
    return BeautifulSoup(resp.text, "html.parser")


def location_name_from_url(url):
    """'/pokearth/kanto/3rd/route3.shtml' → 'Route 3'"""
    slug = url.rstrip("/").split("/")[-1].replace(".shtml", "")
    # Capitalise and humanise
    name = slug.replace("-", " ").replace(".", " ").title()
    # Fix common cases
    name = name.replace("Route", "Route")  # already fine
    return name


# ── Route page parser ─────────────────────────────────────────────────────────

def parse_route_page(soup, url):

    location = location_name_from_url(url)
    sections = []

    for table in soup.find_all("table", class_=["extradextable", "dextable"]):

        classes = [cls for td in table.find_all("td") for cls in (td.get("class", []) or [])]
        
        if "firered" in classes:
            game = "FireRed"
        elif "leafgreen" in classes:
            game = "LeafGreen"
        else:
            game = "FireRed/LeafGreen"
        
        method = ""
        if "grass" in classes:
            method = "by walking in tall grass"
        elif "surf" in classes:
            method = "by using surf"
        elif "fish" in classes:
            fishing_td = table.find("td", class_="fish")
            method = "by fishing with " + (fishing_td.get_text(strip=True))
        elif "gift" in classes:
            method = "as a gift/ trade"

        # Extract parallel columns: name / rate / level
        names  = [td.get_text(strip=True) for td in table.find_all("td", class_="name")]
        rates  = [td.get_text(strip=True) for td in table.find_all("td", class_="rate")]
        levels = [td.get_text(strip=True) for td in table.find_all("td", class_="level")]

        if not names:
            continue

        sentences = []
        for i, name in enumerate(names):
            rate  = rates[i]  if i < len(rates)  else "?"
            level = levels[i] if i < len(levels) else "?"
            sentences.append(
                f"{name} can be found in {location} ({game}) {method} "
                f"at level(s) {level} with a {rate} rate."
            )

        sections.append({
            "heading": f"{location} — Wild Pokémon ({game})",
            "text": " ".join(sentences),
        })

    # ── Trainers ──────────────────────────────────────────────────────────────
    # Each trainer is a separate table.trainer
    trainer_sentences = []
    for table in soup.find_all("table", class_="trainer"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Row 0: sprites (skip)
        # Row 1: trainer name + pokemon names
        name_cells = rows[1].find_all("td")
        if not name_cells:
            continue

        trainer_name = name_cells[0].get_text(strip=True)
        pokemon_names = [
            a.get_text(strip=True)
            for td in name_cells[1:]
            for a in td.find_all("a")
            if a.get_text(strip=True)
        ]

        # Row 2 has level cells
        level_cells = rows[2].find_all("td", class_="level") if len(rows) > 2 else []
        levels = [td.get_text(strip=True) for td in level_cells]

        pokemon_str = ", ".join(
            f"{p} Lv.{l}" if i < len(levels) else p
            for i, (p, l) in enumerate(zip(pokemon_names, levels + ["?"] * len(pokemon_names)))
        )

        if trainer_name and pokemon_str:
            trainer_sentences.append(
                f"Trainer {trainer_name} has: {pokemon_str}."
            )

    if trainer_sentences:
        sections.append({
            "heading": f"{location} — Trainers",
            "text": " ".join(trainer_sentences),
        })

    # ── Items ──────────────────────────────────────────────────────────────────
    # Items table has headers "Item" and "Method" with class fooevo
    item_sentences = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("td", class_="fooevo")]
        if "item" not in headers or "method" not in headers:
            continue
        for row in table.find_all("tr"):
            cells = row.find_all("td", class_="fooinfo")
            if len(cells) >= 2:
                item   = cells[0].get_text(strip=True)
                method = cells[1].get_text(strip=True)
                if item:
                    item_sentences.append(f"Item: {item} — {method}.")

    if item_sentences:
        sections.append({
            "heading": f"{location} — Items",
            "text": " ".join(item_sentences),
        })

    return {
        "page_title": location,
        "source_url": url,
        "sections": sections,
    }


# ── Pokédex page parser ───────────────────────────────────────────────────────

def parse_pokemon_page(soup, url):
    """
    Extracts from a Serebii /pokedex-rs/ page:
      - Basic info: name, type, classification, capture rate, ability
      - FireRed/LeafGreen locations
      - FireRed/LeafGreen level-up moves
      - TM/HM moves learnable
 
    Returns a dict with multiple sections, one per topic.
    """
 
    # ── Pokémon name ──────────────────────────────────────────────────────────
    title_tag = soup.find("title")
    pokemon_name = "Unknown"
    if title_tag:
        parts = title_tag.text.split("-")
        if len(parts) >= 2:
            pokemon_name = parts[-1].strip()
 
    sections = []
 
    # ── Basic info ────────────────────────────────────────────────────────────
    poke_type       = None
    classification  = None
    capture_rate    = None
    ability_name    = None
    ability_desc    = None
 
    for table in soup.find_all("table", class_="dextable"):
        rows = table.find_all("tr")
        for idx, row in enumerate(rows):
 
            # Type — look for typeimg in this row
            if not poke_type:
                type_img = row.find("img", class_="typeimg")
                if type_img:
                    poke_type = type_img.get("alt", "").replace("-type", "").strip()
 
            # Classification / Capture Rate row
            header_texts = [td.get_text(strip=True) for td in row.find_all("td", class_="foo")]
            if "Capture Rate" in header_texts and idx + 1 < len(rows):
                data_cells = rows[idx + 1].find_all("td", class_="fooinfo")
                if len(data_cells) >= 4:
                    classification = data_cells[0].get_text(strip=True)
                    capture_rate   = data_cells[3].get_text(strip=True)
 
            # Ability name
            ability_td = row.find("td", class_="fooleft")
            if ability_td and not ability_name:
                ability_name = ability_td.get_text(strip=True).replace("Ability:", "").strip()
 
            # Ability description (row after fooleft)
            if ability_name and not ability_desc and idx > 0:
                prev_row = rows[idx - 1]
                if prev_row.find("td", class_="fooleft"):
                    desc_td = row.find("td", class_="fooinfo")
                    if desc_td:
                        ability_desc = desc_td.get_text(strip=True)
 
        # Stop once we have everything
        if poke_type and classification and capture_rate and ability_name:
            break
 
    parts = [f"{pokemon_name} is a {poke_type}-type Pokémon." if poke_type else ""]
    if classification:
        parts.append(f"Classification: {classification}.")
    if capture_rate:
        parts.append(f"Capture rate: {capture_rate}.")
    if ability_name:
        ability_str = f"Ability: {ability_name}"
        if ability_desc:
            ability_str += f" — {ability_desc}"
        parts.append(ability_str + ".")
 
    if any(parts):
        sections.append({
            "heading": f"{pokemon_name} — Basic Info",
            "text": " ".join(p for p in parts if p),
        })
 
    # ── Location (FireRed / LeafGreen only) ───────────────────────────────────
    location_anchor = soup.find("a", attrs={"name": "location"})
    if location_anchor:
        location_table = location_anchor.find_next("table", class_="dextable")
        if location_table:
            loc_sentences = []
            for row in location_table.find_all("tr"):
                game_td = row.find("td", class_=["firered", "leafgreen"])
                if not game_td:
                    continue
                game = "FireRed" if "firered" in game_td.get("class", []) else "LeafGreen"
                location_tds = row.find_all("td", class_="fooinfo")
                if not location_tds:
                    continue
                loc_text = location_tds[-1].get_text(strip=True)
                if loc_text and "trade" not in loc_text.lower():
                    loc_sentences.append(
                        f"{pokemon_name} can be found in {game} at: {loc_text}."
                    )
            if loc_sentences:
                sections.append({
                    "heading": f"{pokemon_name} — FireRed & LeafGreen Locations",
                    "text": " ".join(loc_sentences),
                })
 
    # ── Level-up moves ────────────────────────────────────────────────────────
    for table in soup.find_all("table", class_="dextable"):
        thead = table.find("thead")
        if not thead:
            continue
        header_text = thead.get_text()
 
        # Only grab FRLG-specific level up table (skip RSE table)
        if "Fire Red" not in header_text and "Leaf Green" not in header_text:
            continue
        if "Level Up" not in header_text:
            continue
 
        tbody = table.find("tbody")
        if not tbody:
            continue
 
        move_sentences = []
        for row in tbody.find_all("tr"):
            cells = row.find_all("td", class_="fooinfo")
            # Move rows: first cell has no colspan (level), second has move name
            if len(cells) >= 2 and not cells[0].get("colspan"):
                raw_level = cells[0].get_text(strip=True)
                # "—" (em dash) means learned at start / level 1
                level = "the start" if raw_level in ("—", "–", "\u2014", "") else f"level {raw_level}"
                name_link = cells[1].find("a")
                move_name = name_link.get_text(strip=True) if name_link else cells[1].get_text(strip=True)
                if move_name:
                    move_sentences.append(f"{move_name} (learned at {level})")
 
        if move_sentences:
            sections.append({
                "heading": f"{pokemon_name} — Level-Up Moves (FireRed/LeafGreen)",
                "text": f"{pokemon_name} learns the following moves by leveling up in FireRed and LeafGreen: "
                        + ", ".join(move_sentences) + ".",
            })
        break  # only need the FRLG table, stop after first match
 
    # ── TM / HM moves ─────────────────────────────────────────────────────────
    for table in soup.find_all("table", class_="dextable"):
        thead = table.find("thead")
        if not thead:
            continue
        header_text = thead.get_text()
        if "TM" not in header_text and "HM" not in header_text:
            continue
 
        tbody = table.find("tbody")
        if not tbody:
            continue
 
        tms, hms = [], []
        for row in tbody.find_all("tr"):
            cells = row.find_all("td", class_="fooinfo")
            if len(cells) >= 2 and not cells[0].get("colspan"):
                tmhm_id = cells[0].get_text(strip=True)
                name_link = cells[1].find("a")
                move_name = name_link.get_text(strip=True) if name_link else cells[1].get_text(strip=True)
                if tmhm_id.startswith("HM"):
                    hms.append(f"{tmhm_id} {move_name}")
                elif tmhm_id.startswith("TM"):
                    tms.append(f"{tmhm_id} {move_name}")
 
        parts = []
        if tms:
            parts.append(f"{pokemon_name} can learn these TMs: {', '.join(tms)}.")
        if hms:
            parts.append(f"{pokemon_name} can learn these HMs: {', '.join(hms)}.")
        if parts:
            sections.append({
                "heading": f"{pokemon_name} — TM & HM Moves",
                "text": " ".join(parts),
            })
        break  # only one TM/HM table
 
    if not sections:
        return None
 
    return {
        "page_title": f"{pokemon_name} — Pokédex",
        "source_url": url,
        "sections": sections,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def scrape_all(output_dir="data/raw"):
    os.makedirs(output_dir, exist_ok=True)

    all_pages = (
        [("route", url) for url in SEREBII_ROUTE_URLS]
        + [("pokemon", url) for url in SEREBII_POKEMON_URLS]
    )

    for i, (page_type, url) in enumerate(all_pages):
        slug = url.rstrip("/").split("/")[-1].replace(".shtml", "")
        filename = f"{page_type}_{slug}.json"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"[{i+1}/{len(all_pages)}] Skip (exists): {filename}")
            continue

        print(f"[{i+1}/{len(all_pages)}] Scraping: {url}")
        try:
            soup = fetch(url)

            if page_type == "route":
                data = parse_route_page(soup, url)
            else:
                data = parse_pokemon_page(soup, url)

            if data and data.get("sections"):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  Saved {len(data['sections'])} sections → {filename}")
            else:
                print(f"  No sections extracted, skipping.")

        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    scrape_all()
    
    # Debug
    # url = "https://www.serebii.net/pokearth/kanto/3rd/route4.shtml"
    # soup = fetch(url)
    # data = parse_route_page(soup, url)
    # print(data)