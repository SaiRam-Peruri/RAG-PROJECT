# Advanced Proposal Tools

Production-grade tools for federal proposal compliance, tracking, and quality assurance.

## 🎯 Three Core Tools

### 1. **Compliance Matrix Generator** (`compliance_matrix.py`)
Extracts requirements from RFP and builds trackable compliance matrix.

**What it does:**
- Parses RFP for "shall", "must", "will", "should" statements
- Categorizes requirements (Technical, Management, Personnel, Security, etc.)
- Creates Excel matrix with tracking columns
- Identifies mandatory vs. desirable requirements

**When to use:**
- ✅ Immediately after RFP release
- ✅ Before starting proposal writing
- ✅ To assign requirements to proposal team members

**Example:**
```powershell
python compliance_matrix.py
# Select opportunity: CORHQ-25-R-0450
# Output: CORHQ-25-R-0450_Compliance_Matrix.xlsx
```

**Excel Output Columns:**
| Req ID | Category | Type | Requirement Text | Source | Response Location | Compliance Status | Notes |
|--------|----------|------|------------------|--------|-------------------|-------------------|-------|
| REQ-0001 | Technical | Mandatory | The contractor shall implement cloud-native architecture... | Amendment 1, p.15 | _[Team fills in]_ | Not Started | |

### 2. **Requirement Tracker** (`requirement_tracker.py`)
Tracks which requirements are addressed in proposal drafts, shows coverage gaps.

**What it does:**
- Loads requirements from RFP
- Analyzes proposal sections (Word docs or text files)
- Identifies which requirements are addressed
- Generates coverage report showing gaps

**When to use:**
- ✅ After drafting proposal sections
- ✅ Before internal reviews (Red Team/Pink Team)
- ✅ To verify 100% requirement coverage before submission

**Example:**
```powershell
python requirement_tracker.py
# Select opportunity: CORHQ-25-R-0450
# Enter proposal path: ./proposal_drafts/
# Output: CORHQ-25-R-0450_Coverage_Report.txt
```

**Coverage Output:**
```
COVERAGE SUMMARY
================================================================
Total Requirements: 87
Addressed: 73 (83.9%)
Not Addressed: 14

⚠️ WARNING: Coverage below 100%. Review gaps before submission.

Top 5 gaps to address:
  REQ-0023 - Technical Approach
    The contractor shall provide disaster recovery capabilities within 4 hours...
  
  REQ-0045 - Security Requirements
    The contractor shall maintain FedRAMP Moderate authorization...
```

### 3. **Multi-Round Refinement Workflow** (`refinement_workflow.py`)
Iteratively improves proposal sections through automated quality analysis and regeneration.

**What it does:**
- Generates initial draft (v1)
- Analyzes for compliance, quality, completeness issues
- Applies feedback and regenerates improved versions
- Tracks changes between versions
- Calculates quality scores (0-100)

**When to use:**
- ✅ After generating initial section draft
- ✅ When section needs improvement but you're unsure how
- ✅ To systematically address reviewer feedback

**Example:**
```powershell
python refinement_workflow.py
# Enter opportunity: CORHQ-25-R-0450
# Select section: 1 (Technical Approach)

# ROUND 1: Initial Draft → Quality: 72.0/100
# ANALYSIS: Missing disaster recovery details, weak differentiation
# ROUND 2: Refinement → Quality: 84.5/100 (+12.5 improvement)
# ROUND 3: Refinement → Quality: 89.0/100 (+17.0 improvement)

# Output: CORHQ-25-R-0450_technical_REFINED_v3.docx
#         CORHQ-25-R-0450_technical_VERSION_HISTORY.docx
```

**Quality Score Thresholds:**
- 🟢 **85-100**: High quality, ready for review
- 🟡 **70-84**: Good quality, consider one more pass
- 🔴 **<70**: Needs improvement, additional refinement recommended

---

## 🔄 Complete Proposal Workflow

### Phase 1: Opportunity Assessment (Day 1)
```powershell
# 1. Ingest RFP documents
python rag_ingest.py
# → Processes: RFP, amendments, Q&A, technical requirements

# 2. Generate compliance matrix
python compliance_matrix.py
# → Output: Excel matrix with all requirements tracked

# 3. Ask key questions about opportunity
python rag_answer.py
# "What are the evaluation factors?"
# "What are the technical requirements?"
# "What is the NAICS code and size standard?"
```

### Phase 2: Compliance Planning (Day 2-3)
```powershell
# 4. Assign requirements to team members
# Open compliance matrix Excel file
# Assign each requirement to proposal section owner

# 5. Query section-specific requirements
python rag_section_query.py
# → Pull evaluation criteria, technical reqs, past performance needs
```

### Phase 3: Initial Drafting (Week 1)
```powershell
# 6. Generate initial section drafts
python proposal_generator.py
# Select: 1-Technical, 2-Management, 3-Past Performance, 4-Executive Summary
# → Output: {opportunity}_{section}_DRAFT.docx

# Repeat for all sections
```

### Phase 4: Quality Improvement (Week 2)
```powershell
# 7. Refine each section iteratively
python refinement_workflow.py
# → Analyzes drafts, applies feedback, regenerates
# → Tracks versions and improvements

# Continue until quality score ≥85
```

### Phase 5: Compliance Verification (Week 3)
```powershell
# 8. Check requirement coverage
python requirement_tracker.py
# Enter path to all proposal sections
# → Identifies which requirements are NOT addressed

# 9. Address gaps
# Review coverage report
# Update missing content
# Re-run tracker until 100% coverage
```

### Phase 6: Final Review (Week 4)
```powershell
# 10. Final quality checks
python requirement_tracker.py  # Verify 100% coverage
# → All requirements addressed ✅

# 11. Verify compliance matrix
# Open Excel matrix
# Confirm all requirements marked "Completed"
# Confirm all "Response Location" cells populated

# 12. Package proposal for submission
```

---

## 📊 Tool Integration Matrix

| Tool | Input | Output | Integrates With |
|------|-------|--------|----------------|
| `compliance_matrix.py` | RFP docs in DB | Excel matrix | → Used by all writers |
| `proposal_generator.py` | Opportunity + section | Word draft | → Input to refinement |
| `refinement_workflow.py` | Draft + feedback | Improved drafts | ← From proposal_generator |
| `requirement_tracker.py` | Drafts + RFP | Coverage report | ← From refinement workflow |

**Data Flow:**
```
RFP → rag_ingest.py → ChromaDB
                         ↓
           compliance_matrix.py → Excel matrix (team planning)
                         ↓
           proposal_generator.py → Initial drafts
                         ↓
          refinement_workflow.py → Improved drafts (v2, v3, v4...)
                         ↓
          requirement_tracker.py → Coverage verification
                         ↓
                    Final Proposal ✅
```

---

## 🎯 Production Best Practices

### Compliance Matrix
✅ **DO:**
- Generate matrix immediately after RFP release
- Assign requirements to owners within 48 hours
- Update "Compliance Status" daily during drafting
- Use Excel filters to track progress by category

❌ **DON'T:**
- Wait until drafting starts to extract requirements
- Leave "Response Location" empty (shows non-compliance)
- Ignore "Desirable" requirements (they affect scoring)

### Requirement Tracker
✅ **DO:**
- Run tracker after each major draft revision
- Aim for 100% coverage before Pink Team review
- Address gaps in priority order (Mandatory → Desirable)
- Re-run after incorporating feedback

❌ **DON'T:**
- Wait until final review to check coverage
- Assume all requirements are addressed without verification
- Submit with <95% coverage

### Refinement Workflow
✅ **DO:**
- Start with auto-generated analysis feedback
- Track quality improvement across versions
- Stop when score plateaus (marginal improvement <2 points)
- Save version history for audit trails

❌ **DON'T:**
- Over-refine (diminishing returns after 3-4 rounds)
- Ignore specific compliance feedback
- Skip analysis step between rounds

---

## 🚀 Advanced Usage

### Custom Requirement Categories
Edit `compliance_matrix.py` line 60:
```python
categories = {
    'Cloud Architecture': [],
    'DevSecOps': [],
    'AI/ML Capabilities': [],
    # Add domain-specific categories
}
```

### Adjust Quality Scoring
Edit `refinement_workflow.py` line 250:
```python
def _calculate_quality_score(self, content: str, requirements: str) -> float:
    score = 70  # Adjust base score
    
    # Add custom scoring criteria
    if 'our proven approach' in content.lower():
        score += 5  # Bonus for differentiation
```

### Multi-Opportunity Tracking
```powershell
# Generate matrices for all active opportunities
python compliance_matrix.py  # Select Opp 1
python compliance_matrix.py  # Select Opp 2
python compliance_matrix.py  # Select Opp 3

# Consolidate into master tracking spreadsheet
```

---

## 📈 Success Metrics

Track these KPIs for your proposal process:

| Metric | Target | Tool |
|--------|--------|------|
| Time to compliance matrix | <2 hours | compliance_matrix.py |
| Requirement coverage | 100% | requirement_tracker.py |
| Quality score improvement | +15 points | refinement_workflow.py |
| Drafting speed | 2-3 sections/day | proposal_generator.py |
| Review cycles | <3 rounds | refinement_workflow.py |

---

## 🔧 Dependencies

All three tools require:
```bash
pip install chromadb openai openpyxl python-docx colorama
```

**Python packages:**
- `chromadb`: Vector database queries
- `openai`: GPT-4o-mini for analysis and generation
- `openpyxl`: Excel matrix creation
- `python-docx`: Word document handling
- `colorama`: Terminal color output

---

## 🎓 Training Your Team

### For Proposal Managers
1. Run `compliance_matrix.py` after RFP release
2. Assign requirements in Excel matrix
3. Monitor coverage with `requirement_tracker.py`
4. Verify 100% before submission

### For Technical Writers
1. Use `proposal_generator.py` for initial drafts
2. Refine with `refinement_workflow.py`
3. Check your section coverage with `requirement_tracker.py`
4. Update compliance matrix "Response Location"

### For Reviewers (Pink Team/Red Team)
1. Request latest `requirement_tracker.py` report
2. Focus reviews on gaps and low-coverage areas
3. Use quality scores from `refinement_workflow.py` to prioritize
4. Verify compliance matrix is 100% complete

---

## 🆘 Troubleshooting

**Issue:** Compliance matrix shows too many requirements (500+)
- **Solution:** RFP might include FAR clauses. Filter by `stage != 'context'` in line 85

**Issue:** Requirement tracker shows 0% coverage
- **Solution:** Check that proposal files are .docx or .txt format, ensure key terms overlap

**Issue:** Refinement workflow quality score stuck at 70
- **Solution:** Provide more specific feedback, check that requirements are loaded correctly

**Issue:** "No documents found" error
- **Solution:** Verify opportunity name matches exactly, check `python check_opportunities.py` for available opportunities

---

## 📝 Next Enhancements

Future capabilities to add:

1. **Automated Pink Team Review**: AI-powered proposal critique simulating reviewer perspective
2. **Win Probability Scoring**: Analyze drafts against past performance data to predict win likelihood
3. **Discriminator Analysis**: Extract PWin factors and map to proposal content
4. **Cost Volume Integration**: Link technical approach to pricing for consistency
5. **Submission Checklist Generator**: Auto-generate SF-33, SF-1449, checklist from Section L

---

## 📚 Related Documentation

- [SEMANTIC_ROLES_README.md](SEMANTIC_ROLES_README.md) - Role-based document tagging
- [PROPOSAL_GENERATION_README.md](PROPOSAL_GENERATION_README.md) - Section generation workflow
- Federal Acquisition Regulation (FAR) Part 15 - Contracting by Negotiation

---

**Questions?** Check the code comments or run with `--help` flag.
