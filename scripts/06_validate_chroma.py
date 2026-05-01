"""
Phase 2 — Step 5: Validate ChromaDB retrieval works on local CPU.
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = BASE_DIR / "data" / "chroma_db"
EMBEDDING_MODEL = "pritamdeka/S-PubMedBert-MS-MARCO"
COLLECTION_NAME = "hnscc_abstracts"

def main():
    print(f"Loading embedding model on CPU...")
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    print(f" Dim: {model.get_sentence_embedding_dimension()}")
    
    print(f"\nConnecting to ChromaDB at: {CHROMA_DB_PATH}")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f" Collection size: {collection.count()}")
 
    # Test queries
    queries = [
    "HPV positive oropharyngeal cancer prognosis",
    "PD-L1 expression immunotherapy response HNSCC",
    "single cell RNA sequencing head and neck tumor",
    ]
 
    for q in queries:
        print(f"\n{'='*70}")
        print(f"Query: {q}")
        print(f"{'='*70}")
        
        emb = model.encode([q], normalize_embeddings=True)[0].tolist()
        results = collection.query(query_embeddings=[emb], n_results=3)
    
        for i, (pmid, distance, metadata) in enumerate(zip(
        results["ids"][0],
        results["distances"][0],
        results["metadatas"][0]
        )):
            similarity = 1 - distance
            print(f" \n[{i+1}] PMID: {metadata['pmid']} | Similarity: {similarity:.3f} |Distance: {distance:.3f}")
            print(f" Title: {metadata['title'][:100]}...")
            print(f" Year: {metadata['year']}")

if __name__ == "__main__":
 main()