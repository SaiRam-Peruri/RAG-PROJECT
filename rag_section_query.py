"""
Section-Specific Query Examples
Demonstrates intelligent retrieval for different proposal sections.
"""

import os
import chromadb
from chromadb.utils import embedding_functions

from rag_answer import (
    query_for_evaluation_criteria,
    query_for_technical_approach,
    query_for_past_performance,
    query_for_management_plan,
    query_for_instructions,
    query_for_pricing,
    build_context,
    answer_with_openai,
    format_citation,
    dedup_results
)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set.\n")

    # Setup
    client_chroma = chromadb.PersistentClient(path="chroma_db")
    embedder = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-large",
    )
    coll = client_chroma.get_collection("authoritative", embedding_function=embedder)

    # Opportunity filter (optional)
    print("\n=== Opportunity Filter (Optional) ===")
    print("Enter opportunity name to filter (e.g., 'CORHQ-25-R-0450')")
    print("Or press Enter to search ALL opportunities\n")
    opp_input = input("Opportunity filter: ").strip()
    opportunities = [opp_input] if opp_input else None
    
    if opportunities:
        print(f"✓ Filtering to: {opportunities[0]}\n")
    else:
        print("✓ Searching ALL opportunities\n")

    # Example queries for different proposal sections
    examples = {
        "1": {
            "name": "Evaluation Criteria (Section M)",
            "query_func": query_for_evaluation_criteria,
            "prompt": "What are the evaluation factors and how will proposals be scored?"
        },
        "2": {
            "name": "Proposal Instructions (Section L)",
            "query_func": query_for_instructions,
            "prompt": "What are the page limits and formatting requirements?"
        },
        "3": {
            "name": "Technical Requirements (SOW/PWS)",
            "query_func": lambda c, q: query_for_technical_approach(c, q, include_internal=False),
            "prompt": "What are the technical requirements for this project?"
        },
        "4": {
            "name": "Past Performance Requirements",
            "query_func": query_for_past_performance,
            "prompt": "What past performance will be evaluated?"
        },
        "5": {
            "name": "Pricing Instructions",
            "query_func": query_for_pricing,
            "prompt": "What is the pricing structure and CLIN breakdown?"
        },
        "6": {
            "name": "Management Plan Requirements",
            "query_func": query_for_management_plan,
            "prompt": "What management and organizational information is required?"
        }
    }

    print("\n=== Section-Specific Query Examples ===\n")
    print("Choose a section to query:")
    for key, ex in examples.items():
        print(f"{key}. {ex['name']}")
    print("0. Exit\n")

    choice = input("Select (0-6): ").strip()
    
    if choice == "0":
        return
    
    if choice not in examples:
        print("Invalid choice")
        return

    example = examples[choice]
    print(f"\n📋 Querying: {example['name']}")
    print(f"📝 Question: {example['prompt']}\n")

    # Retrieve using section-specific function
    # Pass opportunities parameter based on function signature
    if choice == "3":  # Technical approach has special parameters
        docs, metas = query_for_technical_approach(coll, example["prompt"], include_internal=False, opportunities=opportunities)
    elif choice in ["1", "2", "4", "5"]:  # Functions with question + opportunities
        docs, metas = example["query_func"](coll, example["prompt"], opportunities=opportunities)
    else:  # Management plan (requires question parameter)
        docs, metas = example["query_func"](coll, example["prompt"], opportunities=opportunities)
    
    docs, metas = dedup_results(docs, metas)

    # Build context
    context = build_context(docs, metas)

    print("=== RETRIEVED CONTEXT ===")
    print(f"Found {len(docs)} relevant chunks")
    
    # Show unique opportunities in results
    unique_opps = set(m.get('opportunity', 'unknown') for m in metas)
    print(f"Opportunities: {', '.join(sorted(unique_opps))}")
    
    print("\nSources:")
    for i, m in enumerate(metas, start=1):
        opp = m.get('opportunity', 'unknown')
        print(f"  {i}. {format_citation(m)} [role: {m.get('doc_role', 'N/A')}, opp: {opp}]")
    print()

    # Generate answer
    print("=== GENERATING ANSWER ===\n")
    answer = answer_with_openai(
        question=example["prompt"],
        mode="auth",
        context=context,
        citations=[format_citation(m) for m in metas]
    )

    print("ANSWER:\n")
    print(answer)
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
