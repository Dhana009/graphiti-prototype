# Framework Design Directory Structure

## Visual Tree

```
framework_design/
│
├── README.md                          # Main overview and navigation
├── STATUS.md                          # Project status and progress tracking
├── STRUCTURE.md                       # This file - directory structure
│
├── research/
│   ├── README.md                      # Research documentation overview
│   ├── questions/
│   │   └── TDD_RESEARCH_QUESTIONS.md  # All 15 research questions
│   └── findings/
│       └── README.md                  # Research findings status
│
├── strategies/
│   ├── README.md                      # Strategies documentation
│   └── TOOL_SELECTION_STRATEGY.md     # Cost-optimized tool selection
│
├── templates/
│   ├── README.md                      # Templates documentation
│   └── QDRANT_DOCUMENT_TEMPLATE.md    # Standard document format
│
├── comparisons/
│   ├── README.md                      # Comparisons documentation
│   └── MODEL_COMPARISON_CATEGORY_A.md # Model performance comparison
│
├── summaries/
│   ├── README.md                      # Summaries documentation
│   └── RESEARCH_SESSION_SUMMARY.md    # Complete session summary
│
└── implementation/
    ├── README.md                      # Implementation documentation
    └── IMPLEMENTATION_CHANGES_NEEDED.md # Pending code changes
```

## Directory Purposes

### `/research`
- **Questions:** Research questions organized by category
- **Findings:** Research results and analysis by category

### `/strategies`
- Tool selection strategies
- Workflow definitions
- Decision frameworks

### `/templates`
- Document storage templates
- Format guidelines
- Metadata structures

### `/comparisons`
- Model performance comparisons
- Cost analysis
- Quality evaluations

### `/summaries`
- Session summaries
- Project status
- Established guidelines

### `/implementation`
- Code change requests
- Implementation plans
- Technical improvements

## File Naming Convention
- UPPERCASE for main concepts: `TDD_RESEARCH_QUESTIONS.md`
- Descriptive names: `TOOL_SELECTION_STRATEGY.md`
- Category prefixes: `MODEL_COMPARISON_CATEGORY_A.md`

## Document Organization
- Each directory has a README.md explaining its purpose
- Documents follow Qdrant template format
- All documents stored in Qdrant as primary storage
- Local files for version control and reference

