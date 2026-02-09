"""
Quick script to check what opportunities exist in the database
"""
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("authoritative")

# Get all docs
result = coll.get()
metas = result['metadatas']

# Count by opportunity
from collections import Counter

opps = [m.get('opportunity', 'unknown') for m in metas]
roles = [m.get('doc_role', 'unknown') for m in metas]

print("=== OPPORTUNITIES IN DATABASE ===")
opp_counts = Counter(opps)
for opp, count in sorted(opp_counts.items()):
    print(f"{opp}: {count} chunks")

print("\n=== DOC ROLES IN DATABASE ===")
role_counts = Counter(roles)
for role, count in sorted(role_counts.items()):
    print(f"{role}: {count} chunks")

print("\n=== OPPORTUNITIES WITH EVALUATION_CRITERIA ROLE ===")
eval_opps = [m.get('opportunity') for m in metas if m.get('doc_role') == 'evaluation_criteria']
eval_opp_counts = Counter(eval_opps)
for opp, count in sorted(eval_opp_counts.items()):
    print(f"{opp}: {count} chunks")

if not eval_opp_counts:
    print("(No documents tagged as evaluation_criteria)")
