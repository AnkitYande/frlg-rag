import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
MODEL_PATH  = os.path.join(os.path.dirname(__file__), "models", "all-MiniLM-L6-v2")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
gemini = genai.GenerativeModel("gemini-2.5-flash")

# ── Lazy loaders ──────────────────────────────────────────────────────────────
# Load heavy resources on first request so Flask binds the port immediately
# and Render doesn't time out waiting for the app to start.

_embedder   = None
_collection = None


def get_embedder():
    global _embedder
    if _embedder is None:
        print("Loading embedding model...")
        _embedder = SentenceTransformer(MODEL_PATH)
        print("Embedding model ready.")
    return _embedder


def get_collection():
    global _collection
    if _collection is None:
        print("Connecting to ChromaDB...")
        chroma = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = chroma.get_collection("frlg")
        print("ChromaDB ready.")
    return _collection


# ── Professor Oak system prompt ───────────────────────────────────────────────

SYSTEM_PROMPT = """You are Professor Oak, the renowned Pokémon researcher from Pallet Town.
You are speaking warmly and directly to a young Trainer who has just set out on their Pokémon journey through Kanto in Pokémon FireRed or LeafGreen.

Your personality:
- Wise, encouraging, and grandfatherly — you believe in this young Trainer
- You speak with gentle authority, like a mentor who has seen everything Kanto has to offer
- Occasionally reference your years of research or your own memories of Kanto, but briefly
- Use light Pokémon flavour ("Ah, a fine question for any Trainer!", "Your Pokédex entry for that would say...") without overdoing it
- Keep answers focused and practical — young Trainers need clear guidance, not lectures

Rules:
- Answer ONLY using the context provided below. Do not invent locations, items, or game mechanics.
- If the answer is not in the context, say so honestly: "Hmm, even my research notes don't cover that one, I'm afraid."
- Keep answers concise — 2 to 4 sentences is usually enough unless the question needs detail
- Never break character
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # 1. Embed the question
    vector = get_embedder().encode(question).tolist()

    # 2. Retrieve top chunks from ChromaDB
    results = get_collection().query(
        query_embeddings=[vector],
        n_results=6,
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # 3. Build context block
    context = "\n\n".join(
        f"[Source: {m['section_heading']} / {m['page_title']}]\n{doc}"
        for doc, m in zip(docs, metadatas)
    )

    # 4. Build full prompt
    prompt = f"""{SYSTEM_PROMPT}

--- CONTEXT FROM RESEARCH NOTES ---
{context}
-----------------------------------

Young Trainer's question: {question}

Professor Oak's answer:"""

    # 5. Call Gemini
    response = gemini.generate_content(prompt)
    answer   = response.text.strip()

    # 6. Build chunks list for debug view
    chunks_used = [
        {
            "heading":    m["section_heading"],
            "page_title": m["page_title"],
            "source_url": m["source_url"],
            "source":     m.get("source", "unknown"),
            "preview":    doc[:200],
            "distance":   round(distances[i], 4),
        }
        for i, (doc, m) in enumerate(zip(docs, metadatas))
    ]

    return jsonify({
        "answer": answer,
        "chunks": chunks_used,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)