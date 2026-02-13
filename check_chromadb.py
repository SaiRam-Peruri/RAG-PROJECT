"""Check ChromaDB status - see if it has chunks loaded"""
import chromadb
from chromadb.config import Settings

# Connect to ChromaDB
try:
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get collection
    collection = client.get_or_create_collection(name="federal_contracting")
    
    # Count documents
    count = collection.count()
    
    print("\n" + "="*60)
    print("📊 CHROMADB STATUS")
    print("="*60)
    print(f"Collection: federal_contracting")
    print(f"Total chunks: {count:,}")
    print(f"Location: C:\\Users\\ACER\\RAG-Project\\chroma_db")
    print("="*60)
    
    if count > 0:
        print(f"\n✅ YES - ChromaDB has {count:,} chunks loaded!")
        print("\nYour database is ready for:")
        print("  • Render.com deployment")
        print("  • ngrok API hosting")
        print("  • Lambda RAG queries")
        
        # Show sample
        print("\n📝 Sample query test:")
        results = collection.query(
            query_texts=["company certifications"],
            n_results=2
        )
        if results['documents'] and results['documents'][0]:
            print(f"  Found {len(results['documents'][0])} relevant chunks")
            print(f"  Sample: {results['documents'][0][0][:200]}...")
    else:
        print("\n⚠️ WARNING - ChromaDB is EMPTY!")
        print("\nYou need to populate it first:")
        print("  1. Make sure documents are in Federal_Contracting/")
        print("  2. Run: python rag_ingest.py")
        print("  3. Wait for ingestion to complete")
        print("  4. Run this check again")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nMake sure:")
    print("  • chroma_db folder exists")
    print("  • chromadb is installed: pip install chromadb")
