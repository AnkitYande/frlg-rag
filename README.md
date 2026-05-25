# Professor Oak's Lab — FireRed & LeafGreen AI Guide

A RAG-powered AI assistant that answers questions about Pokemon FireRed and LeafGreen. Ask where to find Pokemon, how to beat Gym Leaders, item locations, and more — answered in character as Professor Oak, grounded in real game data scraped from Bulbapedia and Serebii.

**[Live Demo](https://ankityande.github.io/frlg-rag)**

---

## How It Works

Questions are embedded with `all-MiniLM-L6-v2`, matched against a ChromaDB vector store built from scraped game data, and the top results are passed as context to Gemini 2.5 Flash which responds in character as Professor Oak.

```
User question
    ↓ embed with all-MiniLM-L6-v2 (local)
Query vector
    ↓ cosine similarity search
ChromaDB (vector store)
    ↓ top 6 matching chunks
Context from Bulbapedia + Serebii
    ↓ injected into prompt
Gemini 2.5 Flash
    ↓
Professor Oak's answer
```

---

## Repo Structure

```
frlg-rag/
├── frontend/          # Static site, deployed to GitHub Pages
├── backend/           # Flask API, deployed to Render
├── data/
│   ├── chroma/        # ChromaDB vector store (commit this)
│   ├── chunks.json
│   └── raw/
├── encoder/           # chunker.py + embed.py
└── scraper/           # Bulbapedia + Serebii scrapers
```

## Data Sources

- **Bulbapedia** — all 20 FRLG walkthrough parts (trainers, encounters, items, route descriptions)
- **Serebii** — Kanto route pages filtered to Gen III, and Pokedex pages #001–151 (locations, level-up moves, TMs/HMs)

## Stack

- Embeddings: `all-MiniLM-L6-v2` (sentence-transformers, GPU)
- Vector DB: ChromaDB
- LLM: Gemini 2.5 Flash
- Backend: Flask on Render
- Frontend: Vanilla HTML/CSS/JS on GitHub Pages

---

## Local Development

```bash
conda create -n frlg-rag python=3.12 -y
conda activate frlg-rag
conda install -c conda-forge sqlite -y
pip install -r backend/requirements.txt

# Create a .env file and add your GEMINI_API_KEY

cd backend && python api.py
# open frontend/index.html in your browser
```

The `API_BASE` constant at the top of `frontend/app.js` controls which backend the frontend hits. It defaults to `http://localhost:5000`.

## Deployment

Everything lives in one repo. GitHub Pages serves `frontend/`, Render serves `backend/`.

Render loads the vector DB loacllyfrom the repo at startup (`data/chroma/`).

> Render's free tier spins down after 15 minutes idle. The first request after inactivity takes ~30 seconds to wake up.

---

*Not affiliated with Nintendo or Game Freak. Game data sourced from Bulbapedia and Serebii for personal educational, non-commercial use.*