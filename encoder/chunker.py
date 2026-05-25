import json
import glob
import os


def process_all_files(raw_dir="data/raw", output_path="data/chunks.json"):
    all_chunks = []
    files = sorted(glob.glob(os.path.join(raw_dir, "*.json")))

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            page = json.load(f)

        for section in page["sections"]:
            # Skip sections with very little content
            if len(section["text"].split()) < 10:
                continue

            # Prefix context into the text itself — critical for retrieval quality
            text = f"{page['page_title']} — {section['heading']}: {section['text']}"

            all_chunks.append({
                "text": text,
                "metadata": {
                    "page_title": page["page_title"],
                    "section_heading": section["heading"],
                    "source_url": page["source_url"],
                }
            })

    print(f"Total chunks: {len(all_chunks)}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    return all_chunks


if __name__ == "__main__":
    process_all_files()