# 🧪 Auto-Service Quick Test

Quick test to verify auto-proposal service works correctly.

## Test: Add New File and Watch Auto-Generation

### Before Starting

Make sure you have:
- ✅ OPENAI_API_KEY set in environment
- ✅ Existing ChromaDB with data
- ✅ Federal_Contracting folder structure

### Test Steps

1. **Start Service**
```powershell
python auto_proposal_service.py
```

Wait for: `✅ SERVICE READY - Watching for new RFP files...`

2. **Create Test Opportunity** (in separate terminal)
```powershell
mkdir Federal_Contracting\01_Active_Pursuits\TEST_OPP\01_Government_Issued
```

Service should show:
```
📁 NEW OPPORTUNITY FOLDER: TEST_OPP
✅ Queued for processing: TEST_OPP
```

3. **Add Test Document**
```powershell
# Copy any PDF to test folder
copy Federal_Contracting\01_Active_Pursuits\CORHQ-25-R-0450\01_Government_Issued\*.pdf Federal_Contracting\01_Active_Pursuits\TEST_OPP\01_Government_Issued\
```

Service should show:
```
🔔 NEW FILE DETECTED: [filename].pdf
✅ Queued for processing: TEST_OPP

======================================================================
🚀 PROCESSING JOB: NEW_RFP - TEST_OPP
======================================================================

📥 INGESTING DOCUMENTS for TEST_OPP...
✅ Ingestion complete

📊 GENERATING COMPLIANCE MATRIX for TEST_OPP...
✅ Compliance matrix created

📝 GENERATING ALL SECTIONS for TEST_OPP...
  → Generating technical...
  ✅ technical complete
  [... more sections ...]

✅ PROPOSAL PACKAGE COMPLETE: TEST_OPP
```

4. **Verify Generated Files**
```powershell
ls *.docx | Where-Object {$_.Name -like "TEST_OPP*"}
ls *.xlsx | Where-Object {$_.Name -like "TEST_OPP*"}
```

Expected output:
- TEST_OPP_Compliance_Matrix.xlsx
- TEST_OPP_technical_DRAFT.docx
- TEST_OPP_management_DRAFT.docx
- TEST_OPP_past_performance_DRAFT.docx
- TEST_OPP_executive_summary_DRAFT.docx

5. **Stop Service**
Press `Ctrl + C`

Should show:
```
🛑 Stopping service...
✅ Service stopped
```

### Expected Results

✅ **PASS** if:
- Service detects new folder
- Service detects new file
- All sections generate without errors
- Files appear in workspace
- Service stops cleanly

❌ **FAIL** if:
- No file detection
- Ingestion errors
- Section generation fails
- Files missing

### Cleanup After Test

```powershell
# Remove test files
rm TEST_OPP_*.docx
rm TEST_OPP_*.xlsx

# Remove test folder
rm -r Federal_Contracting\01_Active_Pursuits\TEST_OPP
```

---

## Troubleshooting Test Failures

**Service doesn't detect file:**
- Check file is in `01_Government_Issued/` folder
- Verify file extension is `.pdf`, `.docx`, or `.xlsx`
- Check service logs: `Get-Content auto_proposal_service.log -Tail 20`

**Ingestion fails:**
- Verify OPENAI_API_KEY: `$env:OPENAI_API_KEY`
- Check ChromaDB exists: `ls chroma_db`
- Verify file is not corrupted

**Section generation fails:**
- Check ChromaDB has data: `python check_opportunities.py`
- Verify API key has credits
- Review error in logs

**Files not created:**
- Check workspace permissions
- Verify disk space available
- Check logs for errors

---

## Next Steps After Successful Test

✅ Service is working! Now you can:

1. **Use with real opportunities:**
   - Add actual RFP files to opportunity folders
   - Let service auto-generate proposals

2. **Run continuously:**
   - Start service at beginning of day
   - Leave running in background
   - Add files as RFPs arrive

3. **Integrate into workflow:**
   - Add RFP → Wait 5-10 min → Review generated proposal
   - Use refinement tools on generated sections
   - Track compliance with generated matrix

---

## Performance Expectations

| Metric | Expected Value |
|--------|---------------|
| File detection | < 1 second |
| Opportunity detection | < 1 second |
| Ingestion (50 pages) | 2-3 minutes |
| Compliance matrix | 1-2 minutes |
| Section generation (4 sections) | 3-5 minutes |
| **Total time** | **5-10 minutes** |

---

**Test completed? Start using the auto-service with real RFPs!**

```powershell
python auto_proposal_service.py
# Then just drop RFP files and watch the magic happen
```
