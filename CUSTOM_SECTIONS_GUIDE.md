# Custom Section Configuration Guide

## Overview
The auto-proposal service is now **flexible** - you can configure which sections to generate for each opportunity!

## Default Behavior
If no config file exists, the system generates **4 standard sections**:
1. Executive Summary
2. Technical Approach
3. Management Plan
4. Past Performance

## Supported Sections
The system supports 9 different section types:

| Section ID | Title | Common Use |
|------------|-------|------------|
| `executive_summary` | Executive Summary | Required in almost all proposals |
| `technical` | Technical Approach | Core technical solution |
| `management` | Management Plan | How you'll manage the contract |
| `past_performance` | Past Performance | Proof of capability |
| `staffing` | Staffing Plan | Labor categories, org chart, resumes |
| `quality_assurance` | Quality Assurance | QA/QC processes and metrics |
| `security` | Security and Compliance | FedRAMP, FISMA, NIST 800-53 |
| `transition` | Transition Plan | Incumbent takeover, migration |
| `cost` | Cost Proposal | (Rarely in technical volume) |

## How to Customize Sections

### Step 1: Create Config File
Copy `section_config_example.json` to your opportunity folder:
```
Federal_Contracting/
  01_Active_Pursuits/
    YOUR_OPPORTUNITY/
      section_config.json  <-- Create this file
      01_Government_Issued/
        Final_Solicitations/
```

### Step 2: Edit Config
Example for a complex RFP requiring 7 sections:
```json
{
  "opportunity": "DHS_CYBERSECURITY_2026",
  "sections": [
    {
      "id": "executive_summary",
      "title": "Executive Summary",
      "required": true
    },
    {
      "id": "technical",
      "title": "Technical Approach",
      "required": true
    },
    {
      "id": "security",
      "title": "Security and Compliance",
      "required": true
    },
    {
      "id": "management",
      "title": "Management Plan",
      "required": true
    },
    {
      "id": "staffing",
      "title": "Staffing Plan",
      "required": true
    },
    {
      "id": "quality_assurance",
      "title": "Quality Assurance",
      "required": true
    },
    {
      "id": "past_performance",
      "title": "Past Performance",
      "required": true
    }
  ]
}
```

### Step 3: Drop RFP
When you drop the RFP file, the auto-service will:
1. Check for `section_config.json`
2. Generate only sections with `"required": true`
3. Log which sections are being generated

## Example Use Cases

### Simple Small Business Set-Aside (3 sections)
```json
{
  "opportunity": "SIMPLE_IT_SUPPORT",
  "sections": [
    {"id": "executive_summary", "title": "Executive Summary", "required": true},
    {"id": "technical", "title": "Technical Approach", "required": true},
    {"id": "past_performance", "title": "Past Performance", "required": true}
  ]
}
```

### Complex System Migration (8 sections)
```json
{
  "opportunity": "CLOUD_MIGRATION_2026",
  "sections": [
    {"id": "executive_summary", "title": "Executive Summary", "required": true},
    {"id": "technical", "title": "Technical Approach", "required": true},
    {"id": "transition", "title": "Transition Plan", "required": true},
    {"id": "security", "title": "Security and Compliance", "required": true},
    {"id": "management", "title": "Management Plan", "required": true},
    {"id": "staffing", "title": "Staffing Plan", "required": true},
    {"id": "quality_assurance", "title": "Quality Assurance", "required": true},
    {"id": "past_performance", "title": "Past Performance", "required": true}
  ]
}
```

### Staffing Augmentation (5 sections)
```json
{
  "opportunity": "STAFF_AUG_2026",
  "sections": [
    {"id": "executive_summary", "title": "Executive Summary", "required": true},
    {"id": "technical", "title": "Technical Approach", "required": true},
    {"id": "staffing", "title": "Staffing Plan", "required": true},
    {"id": "management", "title": "Management Plan", "required": true},
    {"id": "past_performance", "title": "Past Performance", "required": true}
  ]
}
```

## Verification
Check the service logs when it starts generating:
```
[DEFAULT] Using standard 4-section format (create section_config.json to customize)
[SECTIONS] Will generate: Executive Summary, Technical Approach, Management Plan, Past Performance
```

or with config:
```
[CONFIG] Using custom sections from section_config.json
[SECTIONS] Will generate: Executive Summary, Technical Approach, Security and Compliance, Management Plan, Staffing Plan, Quality Assurance, Past Performance
```

## Adding New Section Types
If you need a section type not listed above, you can:
1. Add the prompt in `proposal_generator.py` (section_prompts dictionary)
2. Add it to the default_sections list in `auto_proposal_service.py`
3. Use it in your config file

Example custom section:
```json
{
  "id": "training",
  "title": "Training Plan",
  "required": true
}
```

Then add the prompt in `proposal_generator.py`:
```python
'training': (
    "You are writing the Training Plan section of a federal proposal. "
    "Address: (1) Training approach, (2) Curriculum, (3) Delivery methods, (4) Evaluation. "
    "Cite requirements with [Requirement N]."
)
```

## Summary
No more hardcoded 4 sections! Configure exactly what you need for each RFP.
