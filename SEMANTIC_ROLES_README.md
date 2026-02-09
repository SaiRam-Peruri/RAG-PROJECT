# Semantic Role-Based Retrieval Upgrade

## What Was Added

### 1. Semantic Role Metadata (rag_ingest.py)

Added `doc_role` field to metadata extraction that intelligently categorizes documents:

**Government Documents:**
- `evaluation_criteria` - Section M, ratings, evaluation factors
- `instructions` - Section L, proposal prep instructions
- `technical_requirements` - SOW, PWS, specifications
- `pricing` - CLINs, cost instructions
- `amendment_qa` - Amendments and Q&A documents

**Vendor/Internal Documents:**
- `past_performance` - Past performance narratives
- `technical` - Technical approach content
- `management` - Management plans, org charts
- `quality` - Quality assurance plans
- `security` - Security plans
- `personnel` - Resumes, key personnel

### 2. Role-Based Filtering (rag_answer.py)

Updated `query_chroma()` to accept `doc_roles` parameter:

```python
# Filter by specific document roles
docs, metas = query_chroma(
    coll, 
    "What are the evaluation factors?",
    mode="auth",
    doc_roles=["evaluation_criteria", "amendment_qa"]  # Only pull these roles
)
```

### 3. Section-Specific Query Functions

Created 6 specialized query functions for common proposal sections:

| Function | Purpose | Roles Retrieved |
|----------|---------|-----------------|
| `query_for_evaluation_criteria()` | Section M analysis | evaluation_criteria, amendment_qa |
| `query_for_technical_approach()` | Technical requirements | technical_requirements, evaluation_criteria |
| `query_for_past_performance()` | PP requirements & content | past_performance, evaluation_criteria |
| `query_for_management_plan()` | Management requirements | technical_requirements, instructions |
| `query_for_instructions()` | Section L format rules | instructions, amendment_qa |
| `query_for_pricing()` | Cost/price instructions | pricing, evaluation_criteria |

## How to Use

### Step 1: Re-run Ingestion

To add semantic roles to existing documents:

```powershell
python rag_ingest.py
```

This will rebuild the collections with `doc_role` metadata.

### Step 2: Use Section-Specific Queries

**Option A: Use the demo script**

```powershell
python rag_section_query.py
```

Choose from 6 pre-configured section queries.

**Option B: In your own code**

```python
from rag_answer import query_for_evaluation_criteria, build_context

# Get evaluation criteria
docs, metas = query_for_evaluation_criteria(coll)
context = build_context(docs, metas)

# Now generate answer with focused context
```

## Benefits

### Before (General Retrieval)
```python
# Pulls from ALL government docs, including irrelevant sections
docs, metas = query_chroma(coll, "evaluation factors", mode="auth")
# Result: May include Section C (Description), Section J (Attachments), etc.
```

### After (Role-Based Retrieval)
```python
# Pulls ONLY evaluation-related docs
docs, metas = query_for_evaluation_criteria(coll)
# Result: Section M, Technical Acceptability Matrix, relevant amendments only
```

**Impact:**
- ✅ More focused retrieval
- ✅ Less noise in context
- ✅ Better answers
- ✅ Faster generation (fewer tokens)

## Example Workflow: Drafting Technical Approach

```python
# 1. Get technical requirements from RFP
tech_docs, tech_metas = query_for_technical_approach(
    coll, 
    "What are the technical requirements for cloud migration?"
)

# 2. Get evaluation criteria to understand scoring
eval_docs, eval_metas = query_for_evaluation_criteria(coll)

# 3. Combine contexts
all_docs = tech_docs + eval_docs
all_metas = tech_metas + eval_metas

# 4. Generate draft
context = build_context(all_docs, all_metas)
draft = answer_with_openai(
    "Draft a technical approach for cloud migration",
    mode="draft",
    context=context,
    citations=[]
)
```

## Next Steps

### Recommended Enhancements:

1. **Add page/section detection**
   - Parse PDF text to detect "Section M", "7.3.2-17" markers
   - Auto-tag chunks with section numbers

2. **Add confidence scoring**
   - Track which doc_roles produce best answers
   - Re-rank by role relevance

3. **Create proposal templates**
   - Build section-by-section generation workflows
   - Use appropriate query functions per section

4. **Add internal content collection**
   - Separate collection for awarded proposals
   - Query both government + internal with role filtering

## Testing

Verify semantic roles were added correctly:

```python
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
coll = client.get_collection("authoritative")

# Get one result and check metadata
result = coll.query(query_texts=["evaluation"], n_results=1)
print(result["metadatas"][0])
# Should show: {'doc_role': 'evaluation_criteria', ...}
```
