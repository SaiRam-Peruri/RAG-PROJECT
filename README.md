# RAG-Based Federal Proposal Automation System

An intelligent Retrieval-Augmented Generation (RAG) system for automating federal government proposal generation. This system leverages AI to streamline the proposal development process by intelligently retrieving relevant content from past proposals, RFPs, and company resources.

## 🎯 Overview

This system automates the end-to-end proposal development workflow:
- **Automated ingestion** of RFPs, past proposals, and company resources
- **Intelligent retrieval** using ChromaDB vector database
- **AI-powered generation** of proposal sections with citations
- **Compliance tracking** and requirement management
- **Continuous monitoring** for new opportunities

## 📋 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Modules](#core-modules)
- [Workflow](#workflow)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Project Structure](#project-structure)

## ✨ Features

### Core Capabilities
- **Dual Collection System**: Authoritative (RFPs, contracts) and Drafting (past proposals, templates)
- **Multi-Format Support**: PDF, DOCX, XLSX document processing
- **Semantic Search**: OpenAI embeddings (text-embedding-3-large) for accurate retrieval
- **Section Generation**: Context-aware proposal section writing with citations
- **Compliance Matrix**: Automated requirement-to-response mapping
- **Requirement Tracking**: Comprehensive coverage analysis
- **Auto Service**: File system monitoring for hands-free operation

### Advanced Features
- **Template Filling**: Automated population of proposal templates
- **Refinement Workflow**: Iterative improvement system
- **SAM.gov Integration**: Opportunity checking and analysis
- **Custom Section Configuration**: Flexible section definitions
- **Semantic Role Analysis**: Intelligent content categorization

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Federal_Contracting/                    │
│  ┌─────────────────┬──────────────────┬──────────────┐ │
│  │ Company Docs    │ Active Pursuits  │ Past Work    │ │
│  └─────────────────┴──────────────────┴──────────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │ Ingestion
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    ChromaDB Collections                  │
│  ┌────────────────────┬──────────────────────────────┐  │
│  │ Authoritative      │ Drafting                     │  │
│  │ (RFPs, SOWs)       │ (Past Proposals, Templates)  │  │
│  └────────────────────┴──────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ RAG Query
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Generation Engine                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │ • Section Generator  • Compliance Matrix        │    │
│  │ • Template Filler    • Requirement Tracker      │    │
│  │ • Refinement System  • Answer Generator         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────┘
                          │ Output
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Complete Proposal Package                   │
│  • Drafted Sections  • Compliance Matrix                │
│  • Requirement Tracker • Filled Templates               │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Git

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd RAG-Project
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

3. **Install dependencies**
```bash
pip install openai chromadb pypdf python-docx openpyxl tqdm watchdog
```

4. **Set up environment variables**
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# macOS/Linux
export OPENAI_API_KEY=your-api-key-here
```

5. **Initialize folder structure**
Ensure `Federal_Contracting/` directory exists with:
```
Federal_Contracting/
├── 00_Company_Reference/
│   ├── Boilerplate_Content/
│   ├── Past_Performance/
│   ├── Certifications/
│   └── ...
├── 01_Active_Pursuits/
├── 02_Awarded_Contracts/
└── 03_Unsuccessful_Pursuits/
```

## 🎬 Quick Start

### 1. Ingest Documents
```bash
python rag_ingest.py
```
This indexes all documents from `Federal_Contracting/` into ChromaDB.

### 2. Query the System
```bash
python rag_query.py
# Enter your question
# Choose mode: auth (authoritative) or draft (drafting)
```

### 3. Generate Proposal Section
```bash
python proposal_generator.py
# Follow interactive prompts to generate sections
```

### 4. Run Auto Service (Recommended)
```bash
python auto_proposal_service.py
```
Automatically monitors for new RFPs and generates complete proposals.

### 5. Generate Compliance Matrix
```bash
python compliance_matrix.py <opportunity_folder>
```

## 🔧 Core Modules

### Ingestion System
**File**: `rag_ingest.py`

Indexes documents into two collections:
- **Authoritative**: RFPs, SOWs, contracts, requirements
- **Drafting**: Past proposals, templates, boilerplate

```python
# Key features:
- Multi-format parsing (PDF, DOCX, XLSX)
- Intelligent metadata extraction
- Opportunity-based organization
- Stage classification (reference, active, awarded)
```

### Query System
**Files**: `rag_query.py`, `rag_section_query.py`, `rag_answer.py`

Semantic search across document collections with context-aware retrieval.

### Proposal Generator
**File**: `proposal_generator.py`

Generates complete proposal sections with:
- Context from authoritative sources
- Examples from past proposals
- Full citations and references
- Professional formatting

### Auto Service
**File**: `auto_proposal_service.py`

Continuous monitoring service that:
- Watches for new RFP files
- Auto-ingests documents
- Generates proposal sections
- Creates compliance artifacts
- Logs all operations

### Compliance Tools
**Files**: `compliance_matrix.py`, `requirement_tracker.py`

- Maps requirements to responses
- Tracks coverage percentage
- Identifies gaps
- Generates matrices in DOCX format

### Template System
**File**: `template_filler.py`

Automatically fills proposal templates using RAG-retrieved content.

### Analysis Tools
- `analyze_proposal_format.py`: Analyzes proposal structure
- `analyze_sam_format.py`: Parses SAM.gov opportunity data
- `check_opportunities.py`: Monitors new opportunities

### Refinement Workflow
**File**: `refinement_workflow.py`

Iterative improvement system for refining generated content.

## 🔄 Workflow

### Automated Workflow (Recommended)
```
1. Drop RFP in 01_Active_Pursuits/
2. Auto-service detects and processes
3. Complete proposal generated automatically
4. Review and refine as needed
```

### Manual Workflow
```
1. Ingest: python rag_ingest.py
2. Generate: python proposal_generator.py
3. Compliance: python compliance_matrix.py <opportunity>
4. Track: python requirement_tracker.py
5. Refine: python refinement_workflow.py
```

## ⚙️ Configuration

### Document Collection Rules
Edit `rag_ingest.py` to customize:
- File exclusion patterns
- Supported file types
- Metadata extraction
- Collection assignment

### Section Configuration
See `section_config_example.json` for custom section definitions.

### Search Parameters
Adjust in respective query files:
- Number of results (`n_results`)
- Embedding model
- Collection weights

## 📚 Documentation

Detailed guides available:
- [AUTO_SERVICE_README.md](AUTO_SERVICE_README.md) - Automated service setup
- [PROPOSAL_GENERATION_README.md](PROPOSAL_GENERATION_README.md) - Generation workflows
- [TEMPLATE_FILLING_GUIDE.md](TEMPLATE_FILLING_GUIDE.md) - Template system
- [CUSTOM_SECTIONS_GUIDE.md](CUSTOM_SECTIONS_GUIDE.md) - Section customization
- [SEMANTIC_ROLES_README.md](SEMANTIC_ROLES_README.md) - Content classification
- [WORKFLOW_DIAGRAM.md](WORKFLOW_DIAGRAM.md) - Visual workflows
- [ADVANCED_TOOLS_README.md](ADVANCED_TOOLS_README.md) - Advanced features

## 📁 Project Structure

```
RAG-Project/
├── Core RAG System
│   ├── rag_ingest.py              # Document indexing
│   ├── rag_query.py               # Basic search
│   ├── rag_section_query.py       # Section-specific search
│   └── rag_answer.py              # Answer generation
│
├── Proposal Generation
│   ├── proposal_generator.py      # Main generator
│   ├── template_filler.py         # Template automation
│   ├── compliance_matrix.py       # Compliance tracking
│   └── requirement_tracker.py     # Requirement management
│
├── Automation
│   ├── auto_proposal_service.py   # File watcher service
│   └── check_opportunities.py     # SAM.gov monitoring
│
├── Analysis Tools
│   ├── analyze_proposal_format.py
│   ├── analyze_sam_format.py
│   └── refinement_workflow.py
│
├── Data
│   ├── chroma_db/                 # Vector database
│   └── Federal_Contracting/       # Document repository
│
└── Documentation
    ├── README.md                   # This file
    ├── AUTO_SERVICE_README.md
    ├── PROPOSAL_GENERATION_README.md
    └── ...
```

## 🔐 Security Notes

- Never commit API keys or sensitive data
- `.gitignore` excludes sensitive directories
- Keep compliance documents secure
- Review generated content before submission

## 🤝 Best Practices

1. **Organize Documents**: Use proper folder structure in `Federal_Contracting/`
2. **Regular Ingestion**: Re-run `rag_ingest.py` after adding documents
3. **Review Output**: Always review AI-generated content
4. **Cite Sources**: Maintain citation integrity
5. **Version Control**: Track changes to proposals
6. **Test Queries**: Validate retrieval quality regularly

## 🛠️ Troubleshooting

### Common Issues

**ChromaDB not found**
```bash
# Re-ingest documents
python rag_ingest.py
```

**No results returned**
- Check if documents are in correct folders
- Verify OPENAI_API_KEY is set
- Ensure documents aren't excluded by filters

**Generation errors**
- Verify OpenAI API access
- Check rate limits
- Review input query format

## 📊 Performance Tips

- Use specific queries for better retrieval
- Adjust `n_results` based on context needs
- Monitor ChromaDB size
- Regular database optimization
- Cache frequently used results

## 🔮 Future Enhancements

- [ ] Multi-model support (Anthropic, Cohere)
- [ ] Web interface dashboard
- [ ] Collaborative editing features
- [ ] Version comparison tools
- [ ] Integration with proposal management systems
- [ ] Advanced analytics and reporting
- [ ] Automated bid/no-bid analysis

## 📄 License

[Add your license information here]

## 👥 Contributing

[Add contribution guidelines here]

## 📞 Support

For issues and questions:
- Check documentation in project root
- Review logs in `auto_proposal_service.log`
- Examine ChromaDB collections with query tools

---

**Last Updated**: February 2026
**Version**: 1.0.0
