import json
import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

CHUNKS_PATH = "data/chunks.json"
CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "frlg"
MODEL = "models/gemini-embedding-001"


def main():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    total = len(chunks)
    print(f"Loaded {total} chunks")

    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        chroma.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing '{COLLECTION_NAME}' collection")
    except Exception:
        pass
    collection = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "hnsw:search_ef": 200},
    )

    vectors = []
    for i, chunk in enumerate(chunks):
        result = genai.embed_content(model=MODEL, content=chunk["text"])
        vectors.append(result["embedding"])

        if i % 50 == 0:
            print(f"  [{i}/{total}] embedded...")

    print(f"All {total} chunks embedded. Storing in ChromaDB...")

    for i in range(0, total, 500):
        batch = chunks[i:i + 500]
        collection.add(
            ids=[f"chunk_{i + j}" for j in range(len(batch))],
            embeddings=vectors[i:i + 500],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  Stored chunks {i}–{i + len(batch) - 1}")

    print(f"\nDone. {total} chunks stored in {CHROMA_PATH}")


if __name__ == "__main__":
    main()



# LOCAL GPU EMBEDDING - Replacing with Gemini API calls to work better on remote server with low resources.

# from sentence_transformers import SentenceTransformer

# # Load model onto GPU
# model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")

# # Persistent ChromaDB — saves to disk, only embed once
# chroma = chromadb.PersistentClient(path="data/chroma")
# collection = chroma.get_or_create_collection(
#     name="frlg",
#     metadata={"hnsw:space": "cosine"}  # cosine similarity works best for text
# )

# def embed_all(chunks_path="data/chunks.json"):
#     with open(chunks_path, "r", encoding="utf-8") as f:
#         chunks = json.load(f)

#     texts = [c["text"] for c in chunks]
#     metadatas = [c["metadata"] for c in chunks]
#     ids = [f"chunk_{i}" for i in range(len(chunks))]

#     print(f"Embedding {len(chunks)} chunks on GPU...")

#     # sentence-transformers handles batching internally
#     # show_progress_bar gives you a live progress indicator
#     vectors = model.encode(
#         texts,
#         batch_size=64,
#         show_progress_bar=True,
#         device="cuda",
#         convert_to_numpy=True,
#     )

#     print("Storing in ChromaDB...")
#     collection.add(
#         ids=ids,
#         embeddings=vectors.tolist(),
#         documents=texts,
#         metadatas=metadatas,
#     )

#     print(f"Done! {len(chunks)} chunks embedded and saved to data/chroma")


# if __name__ == "__main__":
#     embed_all()