# scraper/embed.py
import json
import chromadb
from sentence_transformers import SentenceTransformer

# Load model onto GPU
model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")

# Persistent ChromaDB — saves to disk, only embed once
chroma = chromadb.PersistentClient(path="data/chroma")
collection = chroma.get_or_create_collection(
    name="frlg",
    metadata={"hnsw:space": "cosine"}  # cosine similarity works best for text
)

def embed_all(chunks_path="data/chunks.json"):
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    print(f"Embedding {len(chunks)} chunks on GPU...")

    # sentence-transformers handles batching internally
    # show_progress_bar gives you a live progress indicator
    vectors = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        device="cuda",
        convert_to_numpy=True,
    )

    print("Storing in ChromaDB...")
    collection.add(
        ids=ids,
        embeddings=vectors.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Done! {len(chunks)} chunks embedded and saved to data/chroma")


if __name__ == "__main__":
    embed_all()