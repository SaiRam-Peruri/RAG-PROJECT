# Template Filling Mode - User Guide

## Overview
The auto-proposal service now supports **TWO MODES**:

1. **Standard Mode** (default) - Creates a new proposal document from scratch
2. **Template Filling Mode** (auto-detected) - Fills in government-provided template documents

## When to Use Template Filling Mode

Use this mode when the government provides a **pre-formatted template document** that you must complete, such as:

- SF-330 forms (Architect-Engineering proposals)
- Pre-formatted RFP response templates with fill-in sections
- Documents with placeholders like "[INSERT YOUR RESPONSE HERE]"
- Forms with sections marked "Offeror shall provide..."

## How Template Filling Works

### Auto-Detection
The system automatically detects template documents by looking for common indicators:

```
✓ [INSERT RESPONSE]
✓ [CONTRACTOR SHALL PROVIDE]
✓ [OFFEROR RESPONSE]
✓ "Offeror shall provide..."
✓ "Contractor shall describe..."
✓ (Please describe)
✓ (Contractor response)
```

If the document has **3 or more** of these indicators in the first 50 paragraphs, it's treated as a template.

### Workflow Example

**Scenario:** Government provides "RFP_Response_Template.docx" (114 pages)

1. **Drop the template** in your opportunity folder:
   ```
   Federal_Contracting/01_Active_Pursuits/MyRFP/01_Government_Issued/Final_Solicitations/
   └── RFP_Response_Template.docx
   ```

2. **Service detects it's a template:**
   ```
   [TEMPLATE DETECTED] Government template document detected!
   [MODE] Switching to TEMPLATE FILLING mode
   ```

3. **System analyzes the template:**
   ```
   [DETECTED] Found 8 fillable sections:
     • 1.0 Executive Summary (2 paragraphs to fill)
     • 2.1 Technical Approach (5 paragraphs to fill)
     • 3.0 Management Plan (3 paragraphs to fill)
     • 4.0 Past Performance (4 paragraphs to fill)
     • 5.0 Staffing Plan (6 paragraphs to fill)
     • 6.0 Quality Assurance (2 paragraphs to fill)
     • 7.0 Security (4 paragraphs to fill)
     • 8.0 Transition Plan (3 paragraphs to fill)
   ```

4. **Auto-generates content for each section** using RAG

5. **Fills in the template** (preserving ALL government formatting):
   - Headers/footers stay intact
   - Page numbers preserved
   - Formatting, fonts, colors unchanged
   - Only placeholder text replaced

6. **Output:** `MyRFP_FILLED_TEMPLATE.docx`

## Template Format Requirements

### Supported: .docx (Word)
✅ Works with Word documents (.docx, .doc)  
✅ Detects fillable sections automatically  
✅ Preserves all formatting

### Not Yet Supported: PDF Form Fields
❌ PDF with fillable form fields - **not yet implemented**  
**Workaround:** Ask government for Word version of template

## Manual Template Filling

If auto-detection fails or you want manual control:

```powershell
python template_filler.py "path/to/template.docx" "OPPORTUNITY_NAME"
```

Example:
```powershell
python template_filler.py "Federal_Contracting/01_Active_Pursuits/DHS_RFP/01_Government_Issued/Final_Solicitations/Response_Template.docx" "DHS_RFP"
```

## Template Section Mapping

The system automatically maps government template sections to content types:

| Template Heading Contains | Maps To | Generated Content |
|---------------------------|---------|-------------------|
| "Executive Summary" | executive_summary | Concise overview, win themes |
| "Technical Approach" | technical | Technical solution, implementation |
| "Technical Solution" | technical | Same as above |
| "Management" | management | Org structure, QA, risk mgmt |
| "Past Performance" | past_performance | Relevant contract examples |
| "Relevant Experience" | past_performance | Same as above |
| "Staffing" | staffing | Personnel, org chart, qualifications |
| "Personnel" | staffing | Same as above |
| "Quality" | quality_assurance | QA/QC processes, metrics |
| "Security" | security | Security controls, compliance |
| "Compliance" | security | Same as above |
| "Transition" | transition | Transition plan, knowledge transfer |
| "Cost" | cost | Cost breakdown, pricing |

## Comparison: Standard vs Template Mode

| Feature | Standard Mode | Template Filling Mode |
|---------|---------------|----------------------|
| **Input** | RFP requirements document | Government template + RFP |
| **Output** | New proposal (Sam's format) | Filled government template |
| **Formatting** | Creates professional format | Preserves government format |
| **Sections** | Configurable (section_config.json) | Detects from template |
| **Cover Page** | Auto-generates | Uses template's cover |
| **TOC** | Auto-generates | Uses template's TOC |
| **Page Numbers** | Auto-generates | Preserves template's |

## Troubleshooting

### Template Not Detected
**Problem:** System creates new document instead of filling template

**Solution:** 
1. Check if template has fill indicators (see auto-detection list above)
2. Manually run: `python template_filler.py template.docx OPP_NAME`
3. Ensure file is .docx (not PDF)

### No Fillable Sections Found
**Problem:** `[WARN] No fillable sections detected in template!`

**Cause:** Template doesn't have standard fill indicators

**Solution:**
- Check if template has explicit placeholders
- Look for hidden text or comments
- Contact government for clarification
- Manually identify sections to fill

### PDF Template
**Problem:** Government provides PDF template

**Solution:**
1. **Best:** Request Word version from contracting officer
2. **Alternative:** Convert PDF to Word using Adobe Acrobat or online converter
3. **Last Resort:** Create standard proposal, then manually copy into PDF

## Example Use Cases

### Case 1: Simple Template (4 sections)
```
Government provides: "Small_Business_Response_Template.docx"

Contains:
- Executive Summary [INSERT RESPONSE]
- Technical Capabilities [DESCRIBE YOUR APPROACH]
- Past Projects [LIST RELEVANT EXPERIENCE]
- Pricing [PROVIDE COST BREAKDOWN]

Result: 4 sections auto-filled
```

### Case 2: Complex Template (10+ sections)
```
Government provides: "Enterprise_IT_RFP_Response_Template.docx" (114 pages)

Contains:
- Multiple subsections with [CONTRACTOR RESPONSE] placeholders
- Pre-formatted tables to complete
- Specific page limits per section

Result: All placeholder sections auto-filled, tables populated
```

### Case 3: Hybrid Approach
```
1. Auto-fill template with generated content
2. Review MyRFP_FILLED_TEMPLATE.docx
3. Edit sections that need customization
4. Add company-specific details (contacts, certifications)
5. Final review and submit
```

## Best Practices

1. **Always review filled templates** - AI-generated content needs human review
2. **Check page limits** - Templates often have section page limits
3. **Verify formatting** - Ensure filling didn't break tables or formatting
4. **Add company specifics** - Contact info, certifications, signatures
5. **Test before deadline** - Fill template early to catch issues

## Future Enhancements

🚧 **Coming Soon:**
- PDF form field filling
- Table cell filling (for pre-formatted response matrices)
- Smart page limit adherence (auto-summarize if over limit)
- Multi-document template handling (separate technical/cost volumes)

## Summary

**Standard Mode:** Government gives you freedom to format → Create professional proposal from scratch

**Template Mode:** Government specifies exact format → Fill their template automatically

Both modes use the same RAG engine to generate content from RFP requirements and internal best practices!
