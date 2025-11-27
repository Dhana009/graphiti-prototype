# Framework Design Documentation

## Overview
This directory contains all documentation, strategies, templates, and research findings related to the TDD (Test-Driven Development) framework design for AI-assisted development.

## Directory Structure

```
framework_design/
├── README.md (this file)
├── research/
│   ├── questions/          # Research questions by category
│   └── findings/           # Research results and findings
├── strategies/
│   └── tool_selection/     # Tool selection strategies and workflows
├── templates/
│   └── qdrant/             # Document storage templates
├── comparisons/
│   └── models/             # Model comparison studies
├── summaries/
│   └── sessions/           # Session summaries and status
└── implementation/
    └── changes/            # Implementation change requests
```

## Purpose
- **Research:** Questions and findings for TDD framework design
- **Strategies:** Tool selection, cost optimization, and workflow strategies
- **Templates:** Standard formats for document storage in Qdrant
- **Comparisons:** Model performance and cost comparisons
- **Summaries:** Session summaries and project status
- **Implementation:** Change requests and implementation plans

## Document Storage
All documents are stored in **Qdrant** as the primary storage. Local files in this directory are for:
- Version control
- Easy reference during development
- Documentation review

## Key Documents

### Research
- `research/questions/TDD_RESEARCH_QUESTIONS.md` - All 15 research questions organized by category

### Strategies
- `strategies/TOOL_SELECTION_STRATEGY.md` - Cost-optimized tool selection strategy

### Templates
- `templates/QDRANT_DOCUMENT_TEMPLATE.md` - Standard format for Qdrant document storage

### Comparisons
- `comparisons/MODEL_COMPARISON_CATEGORY_A.md` - Model performance comparison for Category A

### Summaries
- `summaries/RESEARCH_SESSION_SUMMARY.md` - Complete session summary and guidelines

### Implementation
- `implementation/IMPLEMENTATION_CHANGES_NEEDED.md` - Pending implementation changes

## Version Control
- Documents are versioned using semantic versioning (major.minor)
- Status tracked: `active` or `deprecated`
- Changes documented in document metadata

## Quick Access
To find documents in Qdrant, search with:
- Research questions: `"TDD research questions"`
- Tool strategy: `"tool selection strategy"`
- Document template: `"Qdrant document template"`
- Model comparison: `"model comparison"`

## Maintenance
- Keep documents organized by category
- Update README files when adding new documents
- Mark deprecated documents with replacement references
- Store all final versions in Qdrant

