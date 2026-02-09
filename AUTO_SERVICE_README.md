# 🤖 Auto-Proposal Service - Complete Automation

**Fully automated proposal generation system that watches for new RFP files and generates complete proposal packages automatically.**

---

## 🎯 What It Does

**DROP RFP FILE → COMPLETE PROPOSAL GENERATED**

The service runs continuously in the background, watching your `Federal_Contracting/01_Active_Pursuits/` folder. When you add a new RFP:

1. ✅ **Auto-detects** new file
2. ✅ **Auto-ingests** to ChromaDB
3. ✅ **Auto-generates** compliance matrix
4. ✅ **Auto-drafts** all proposal sections:
   - Technical Approach
   - Management Plan
   - Past Performance
   - Executive Summary
5. ✅ **Complete proposal package** ready in minutes

**Zero manual intervention required.**

---

## 🚀 Quick Start

### Step 1: Start the Service

```powershell
python auto_proposal_service.py
```

**You'll see:**
```
======================================================================
🚀 AUTO-PROPOSAL SERVICE STARTING
======================================================================
Workspace: C:\Users\ACER\RAG-Project
Watching: C:\Users\ACER\RAG-Project\Federal_Contracting\01_Active_Pursuits
======================================================================
👀 File watcher active
⚙️ Job processor active

✅ SERVICE READY - Watching for new RFP files...
```

### Step 2: Add RFP Files

**Just drag & drop or copy RFP files into the correct folder:**

```
Federal_Contracting/
  └─ 01_Active_Pursuits/
      └─ YOUR_OPPORTUNITY_NAME/
          └─ 01_Government_Issued/
              ├─ RFP_Document.pdf         ← Drop here
              ├─ Amendment_1.pdf          ← Drop here
              └─ Technical_Requirements.xlsx  ← Drop here
```

### Step 3: Watch the Magic Happen

**Service automatically:**
```
🔔 NEW FILE DETECTED: RFP_Document.pdf
✅ Queued for processing: YOUR_OPPORTUNITY_NAME

======================================================================
🚀 PROCESSING JOB: NEW_RFP - YOUR_OPPORTUNITY_NAME
======================================================================

📥 INGESTING DOCUMENTS for YOUR_OPPORTUNITY_NAME...
✅ Ingestion complete

📊 GENERATING COMPLIANCE MATRIX for YOUR_OPPORTUNITY_NAME...
✅ Compliance matrix created: YOUR_OPPORTUNITY_NAME_Compliance_Matrix.xlsx

📝 GENERATING ALL SECTIONS for YOUR_OPPORTUNITY_NAME...
  → Generating technical...
  ✅ technical complete
  → Generating management...
  ✅ management complete
  → Generating past_performance...
  ✅ past_performance complete
  → Generating executive_summary...
  ✅ executive_summary complete

======================================================================
✅ PROPOSAL PACKAGE COMPLETE: YOUR_OPPORTUNITY_NAME
======================================================================

Generated files:
  📊 YOUR_OPPORTUNITY_NAME_Compliance_Matrix.xlsx
  📝 YOUR_OPPORTUNITY_NAME_technical_DRAFT.docx
  📝 YOUR_OPPORTUNITY_NAME_management_DRAFT.docx
  📝 YOUR_OPPORTUNITY_NAME_past_performance_DRAFT.docx
  📝 YOUR_OPPORTUNITY_NAME_executive_summary_DRAFT.docx

🎉 Ready for review!
```

### Step 4: Review Your Proposal

All files are generated in your workspace root:
- Open Word documents to review sections
- Open Excel matrix to track compliance
- Use refinement tools if needed

---

## 📁 Folder Structure Requirements

**For auto-detection to work, use this structure:**

```
Federal_Contracting/
  └─ 01_Active_Pursuits/
      └─ OPPORTUNITY_NAME/              ← Opportunity identifier
          └─ 01_Government_Issued/      ← Service watches this folder
              ├─ Final_Solicitations/
              ├─ Draft_Solicitations/
              └─ Amendments_QA/
```

**Examples:**
```
Federal_Contracting/01_Active_Pursuits/CORHQ-25-R-0450/01_Government_Issued/
Federal_Contracting/01_Active_Pursuits/DMS_Support/01_Government_Issued/
Federal_Contracting/01_Active_Pursuits/ICE_IHSC/01_Government_Issued/
```

---

## 🔍 What Triggers Auto-Generation

### ✅ Monitored Events

| Event | Action |
|-------|--------|
| **New PDF added** | Auto-ingest → Generate proposal |
| **New Word doc added** | Auto-ingest → Generate proposal |
| **New Excel added** | Auto-ingest → Generate proposal |
| **Amendment posted** | Auto-ingest → Update proposal |
| **New opportunity folder** | Monitor for files |

### ❌ Ignored Events

- Files in `02_Industry_Responses/` (your responses, not government)
- Files in `03_Capture_and_Strategy/` (internal docs)
- Temp files starting with `~` or `.`
- Files outside `01_Government_Issued/`

---

## ⚙️ Supported File Types

The service monitors:
- ✅ PDF (`.pdf`)
- ✅ Word (`.docx`, `.doc`)
- ✅ Excel (`.xlsx`, `.xls`)

---

## 🎛️ Service Management

### Start Service
```powershell
python auto_proposal_service.py
```

### Stop Service
Press `Ctrl + C` in the terminal

### Check Service Logs
All activity is logged to:
```
auto_proposal_service.log
```

View logs:
```powershell
Get-Content auto_proposal_service.log -Tail 50 -Wait
```

### Run as Background Process (PowerShell)
```powershell
Start-Process python -ArgumentList "auto_proposal_service.py" -WindowStyle Hidden
```

---

## 🔄 Complete Workflow Example

**Scenario: New RFP for USCIS_CSAI opportunity**

### 1. Create Opportunity Folder (Optional)
```powershell
mkdir Federal_Contracting\01_Active_Pursuits\USCIS_CSAI\01_Government_Issued
```

Service detects:
```
📁 NEW OPPORTUNITY FOLDER: USCIS_CSAI
✅ Queued for processing: USCIS_CSAI
```

### 2. Add RFP Documents
Copy these files:
- `USCIS_CSAI_RFP.pdf`
- `USCIS_CSAI_SOW.docx`
- `USCIS_CSAI_Pricing_Template.xlsx`

To:
- `Federal_Contracting\01_Active_Pursuits\USCIS_CSAI\01_Government_Issued\`

Service detects each file:
```
🔔 NEW FILE DETECTED: USCIS_CSAI_RFP.pdf
✅ Queued for processing: USCIS_CSAI

🔔 NEW FILE DETECTED: USCIS_CSAI_SOW.docx
✅ Already queued: USCIS_CSAI

🔔 NEW FILE DETECTED: USCIS_CSAI_Pricing_Template.xlsx
✅ Already queued: USCIS_CSAI
```

### 3. Auto-Processing Begins
```
======================================================================
🚀 PROCESSING JOB: NEW_RFP - USCIS_CSAI
======================================================================

📥 INGESTING DOCUMENTS for USCIS_CSAI...
Processing: USCIS_CSAI_RFP.pdf (35 pages)
Processing: USCIS_CSAI_SOW.docx (18 pages)
Processing: USCIS_CSAI_Pricing_Template.xlsx (3 sheets)
✅ Ingestion complete

📊 GENERATING COMPLIANCE MATRIX for USCIS_CSAI...
Extracted 127 requirement statements
✅ Compliance matrix created: USCIS_CSAI_Compliance_Matrix.xlsx

📝 GENERATING ALL SECTIONS for USCIS_CSAI...
  → Generating technical...
  ✅ technical complete (2,450 words)
  → Generating management...
  ✅ management complete (1,850 words)
  → Generating past_performance...
  ✅ past_performance complete (1,200 words)
  → Generating executive_summary...
  ✅ executive_summary complete (650 words)

✅ Generated 4/4 sections
```

### 4. Review Generated Files
Files appear in your workspace:
- `USCIS_CSAI_Compliance_Matrix.xlsx`
- `USCIS_CSAI_technical_DRAFT.docx`
- `USCIS_CSAI_management_DRAFT.docx`
- `USCIS_CSAI_past_performance_DRAFT.docx`
- `USCIS_CSAI_executive_summary_DRAFT.docx`

**Total time: 5-10 minutes** (depending on RFP size)

---

## 🛡️ Safety Features

### Duplicate Prevention
- Tracks processed files
- Won't re-process same file multiple times
- Uses file path as unique identifier

### Error Handling
- Logs all errors to `auto_proposal_service.log`
- Continues processing other jobs if one fails
- Timeout protection (10 min per ingestion)

### Queue Management
- Jobs processed sequentially (no conflicts)
- First-in, first-out (FIFO) order
- Thread-safe queue implementation

---

## 🎨 Customization

### Change Watched Folders
Edit `auto_proposal_service.py` line 42:
```python
self.watch_folders = [
    '01_Government_Issued',
    'Draft_Solicitations',
    'Final_Solicitations',
    'Amendments_QA',
    'Your_Custom_Folder'  # Add here
]
```

### Change Section Types
Edit `auto_proposal_service.py` line 198:
```python
sections = [
    'technical', 
    'management', 
    'past_performance', 
    'executive_summary',
    'pricing',           # Add custom sections
    'quality_assurance'  # Add custom sections
]
```

### Adjust Processing Delays
Edit `auto_proposal_service.py` line 219:
```python
time.sleep(2)  # Delay between sections (seconds)
```

---

## 🐛 Troubleshooting

### Service Not Detecting Files

**Problem:** Files added but nothing happens

**Solutions:**
1. Check service is running: Look for "✅ SERVICE READY" message
2. Verify folder structure: Files must be in `01_Government_Issued/`
3. Check file extension: Must be `.pdf`, `.docx`, or `.xlsx`
4. Check logs: `Get-Content auto_proposal_service.log -Tail 20`

### Ingestion Fails

**Problem:** "❌ Ingestion failed" error

**Solutions:**
1. Check OPENAI_API_KEY is set: `$env:OPENAI_API_KEY`
2. Verify ChromaDB folder exists: `chroma_db/`
3. Check file is not corrupted
4. Check disk space

### Section Generation Fails

**Problem:** "⚠️ {section} failed" warning

**Solutions:**
1. Check opportunity has RFP documents ingested
2. Verify ChromaDB has data: `python check_opportunities.py`
3. Check API rate limits (OpenAI)
4. Review error in logs

### Service Stops Unexpectedly

**Problem:** Service exits without Ctrl+C

**Solutions:**
1. Check logs for error messages
2. Verify Python packages installed: `pip list | Select-String watchdog`
3. Check system resources (RAM, CPU)
4. Restart service with fresh terminal

---

## 📊 Performance Metrics

**Typical Processing Times:**

| Task | Time |
|------|------|
| File detection | < 1 second |
| Ingestion (50-page RFP) | 2-3 minutes |
| Compliance matrix | 1-2 minutes |
| Single section draft | 30-60 seconds |
| Complete proposal (4 sections) | 5-10 minutes |

**System Requirements:**
- Python 3.8+
- 4GB RAM minimum
- Stable internet (OpenAI API calls)
- 500MB disk space per opportunity

---

## 🎯 Integration with Other Tools

### Use Manual Tools on Auto-Generated Proposals

After auto-generation completes, you can still use:

**Refinement:**
```powershell
python refinement_workflow.py
# Select the auto-generated opportunity
# Refine specific sections
```

**Coverage Check:**
```powershell
python requirement_tracker.py
# Point to auto-generated Word docs
# Verify 100% requirement coverage
```

**Q&A:**
```powershell
python rag_answer.py
# Ask questions about the opportunity
# System auto-detects opportunity from query
```

---

## 🚦 Service Status Indicators

Watch for these logs:

| Icon | Meaning |
|------|---------|
| 🚀 | Service starting/processing job |
| 👀 | File watcher active |
| ⚙️ | Job processor active |
| 🔔 | New file detected |
| 📁 | New opportunity folder detected |
| 📥 | Ingesting documents |
| 📊 | Generating compliance matrix |
| 📝 | Generating proposal sections |
| ✅ | Task completed successfully |
| ⚠️ | Warning (non-critical) |
| ❌ | Error (critical) |
| 🎉 | Proposal package complete |
| 🛑 | Service stopping |

---

## 📝 Example Log Output

```
2026-02-05 14:32:15 [INFO] ======================================================================
2026-02-05 14:32:15 [INFO] 🚀 AUTO-PROPOSAL SERVICE STARTING
2026-02-05 14:32:15 [INFO] ======================================================================
2026-02-05 14:32:15 [INFO] Workspace: C:\Users\ACER\RAG-Project
2026-02-05 14:32:15 [INFO] Watching: C:\Users\ACER\RAG-Project\Federal_Contracting\01_Active_Pursuits
2026-02-05 14:32:15 [INFO] ======================================================================
2026-02-05 14:32:15 [INFO] 👀 File watcher active
2026-02-05 14:32:15 [INFO] ⚙️ Job processor active
2026-02-05 14:32:15 [INFO] 
2026-02-05 14:32:15 [INFO] ✅ SERVICE READY - Watching for new RFP files...
2026-02-05 14:32:15 [INFO] 
2026-02-05 14:35:22 [INFO] 🔔 NEW FILE DETECTED: CORHQ_Amendment_3.pdf
2026-02-05 14:35:22 [INFO] ✅ Queued for processing: CORHQ-25-R-0450
2026-02-05 14:35:22 [INFO] 
2026-02-05 14:35:22 [INFO] ======================================================================
2026-02-05 14:35:22 [INFO] 🚀 PROCESSING JOB: AMENDMENT - CORHQ-25-R-0450
2026-02-05 14:35:22 [INFO] ======================================================================
2026-02-05 14:35:22 [INFO] 
2026-02-05 14:35:23 [INFO] 📥 INGESTING DOCUMENTS for CORHQ-25-R-0450...
2026-02-05 14:37:45 [INFO] ✅ Ingestion complete
2026-02-05 14:37:48 [INFO] 📊 GENERATING COMPLIANCE MATRIX for CORHQ-25-R-0450...
2026-02-05 14:38:12 [INFO] ✅ Compliance matrix created: CORHQ-25-R-0450_Compliance_Matrix.xlsx
2026-02-05 14:38:14 [INFO] 📝 GENERATING ALL SECTIONS for CORHQ-25-R-0450...
2026-02-05 14:38:14 [INFO]   → Generating technical...
2026-02-05 14:39:02 [INFO]   ✅ technical complete
2026-02-05 14:39:04 [INFO]   → Generating management...
2026-02-05 14:39:48 [INFO]   ✅ management complete
2026-02-05 14:39:50 [INFO]   → Generating past_performance...
2026-02-05 14:40:22 [INFO]   ✅ past_performance complete
2026-02-05 14:40:24 [INFO]   → Generating executive_summary...
2026-02-05 14:40:51 [INFO]   ✅ executive_summary complete
2026-02-05 14:40:51 [INFO] ✅ Generated 4/4 sections
2026-02-05 14:40:51 [INFO] 
2026-02-05 14:40:51 [INFO] ======================================================================
2026-02-05 14:40:51 [INFO] ✅ PROPOSAL PACKAGE COMPLETE: CORHQ-25-R-0450
2026-02-05 14:40:51 [INFO] ======================================================================
2026-02-05 14:40:51 [INFO] 
2026-02-05 14:40:51 [INFO] Generated files:
2026-02-05 14:40:51 [INFO]   📊 CORHQ-25-R-0450_Compliance_Matrix.xlsx
2026-02-05 14:40:51 [INFO]   📝 CORHQ-25-R-0450_technical_DRAFT.docx
2026-02-05 14:40:51 [INFO]   📝 CORHQ-25-R-0450_management_DRAFT.docx
2026-02-05 14:40:51 [INFO]   📝 CORHQ-25-R-0450_past_performance_DRAFT.docx
2026-02-05 14:40:51 [INFO]   📝 CORHQ-25-R-0450_executive_summary_DRAFT.docx
2026-02-05 14:40:51 [INFO] 
2026-02-05 14:40:51 [INFO] 🎉 Ready for review!
2026-02-05 14:40:51 [INFO] 
```

---

## 🎓 Best Practices

### 1. Keep Service Running During Work Hours
Start service at beginning of day, let it watch continuously

### 2. Organize Files Before Adding
Create opportunity folder first, then add all RFP documents at once

### 3. Monitor Logs Periodically
Check logs to ensure processing completes successfully

### 4. Review Generated Proposals Promptly
Auto-generated proposals are drafts - review and refine same day

### 5. Use Refinement Tools
Run `refinement_workflow.py` on critical sections

### 6. Verify Compliance Matrix
Open Excel matrix and assign requirements to team members

---

## 🔮 Future Enhancements

Planned features:
- [ ] Email notifications when proposal complete
- [ ] Slack/Teams integration
- [ ] Auto-upload to SharePoint/OneDrive
- [ ] Parallel section generation (faster)
- [ ] Custom section templates
- [ ] Auto-requirement tracker integration
- [ ] Web dashboard for monitoring
- [ ] Mobile app notifications

---

## ❓ FAQ

**Q: Can I add files while service is processing another job?**  
A: Yes! Files are queued and processed sequentially.

**Q: What happens if I add the same file twice?**  
A: It's ignored. Service tracks processed files.

**Q: Can multiple people use the same service?**  
A: Yes, but only one service instance per workspace. Use shared folder.

**Q: Does this work on Mac/Linux?**  
A: Yes! Service is cross-platform (Python).

**Q: How much does auto-generation cost (OpenAI)?**  
A: ~$2-5 per complete proposal (4 sections + matrix).

**Q: Can I customize the sections generated?**  
A: Yes! Edit the `sections` list in the code (line 198).

**Q: Does this replace manual proposal writing?**  
A: No - it creates DRAFTS. Always review, refine, and customize.

---

## 📞 Support

**Logs:** Check `auto_proposal_service.log` for detailed error messages  
**Test:** Use existing CORHQ-25-R-0450 documents to verify setup  
**Issues:** Review error messages and check troubleshooting section  

---

**🎉 You now have a fully automated proposal generation system!**

Just start the service and drop RFP files - complete proposals appear automatically.
