import os
import chromadb
from chromadb.utils import embedding_functions

COLL_AUTH = "authoritative"
COLL_DRAFT = "drafting"

def main():
    q = input("Ask: ").strip()
    mode = input("Mode (auth/draft): ").strip().lower()

    client = chromadb.PersistentClient(path="chroma_db")
    embedder = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-large",
    )

    coll = client.get_collection(COLL_AUTH if mode.startswith("a") else COLL_DRAFT, embedding_function=embedder)

    # basic retrieval
    res = coll.query(query_texts=[q], n_results=5)

    print("\nTop matches:\n")
    for i in range(len(res["ids"][0])):
        meta = res["metadatas"][0][i]
        doc = res["documents"][0][i]
        print(f"[{i+1}] {meta.get('filename')} | stage={meta.get('stage')} | opp={meta.get('opportunity')} | page={meta.get('page')}")
        print(doc[:600].replace("\n"," ") + " ...\n")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set.")
    main()
