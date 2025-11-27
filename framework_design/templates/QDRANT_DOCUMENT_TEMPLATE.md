# Qdrant Document Storage Template

## Purpose
This template defines the standard format for storing documents in Qdrant to ensure easy semantic search and retrieval.

---

## Document Structure Template

### Format:
```
DOCUMENT TITLE: [Clear, Descriptive Title]

SUMMARY: [1-2 sentence summary of the document's purpose and key content]

[MAIN CONTENT ORGANIZED BY SECTIONS]

SECTION 1: [Section Title]
[Content with clear structure]

SECTION 2: [Section Title]
[Content with clear structure]

KEY POINTS:
- Point 1
- Point 2
- Point 3

EXAMPLES:
[Concrete examples if applicable]

---

METADATA (for Qdrant payload):
- doc_id: [unique identifier]
- title: [document title]
- category: [reference/research_summary/test_pattern/etc]
- document_type: [tool_selection_strategy/research_findings/etc]
- purpose: [cost_optimization/research_guidance/etc]
- key_topics: [array of main topics]
- version: [version number]
- status: [active/deprecated]
- priority: [critical/high/medium/low]
- created_at: [timestamp]
- updated_at: [timestamp]
```

---

## Detailed Template Structure

### 1. Document Header (First 3-5 lines)
```
DOCUMENT TITLE: [Clear, Descriptive Title in UPPERCASE]

SUMMARY: [1-2 sentence summary that captures the essence]
- What this document contains
- Why it's important
- When to use it
```

### 2. Core Content Sections
Use clear section headers in UPPERCASE:
- `SECTION NAME:` or `CATEGORY NAME:`
- Keep sections focused and semantically coherent
- Use bullet points for lists
- Use tables for comparisons
- Include code examples when relevant

### 3. Key Information Placement
- **Keywords naturally embedded** in the text (don't stuff)
- **Explicit key points** listed at the end of major sections
- **Examples** provided for clarity
- **Quick reference** sections for fast lookup

### 4. Metadata Structure (Qdrant Payload)
```json
{
  "doc_id": "doc_[unique_id]",
  "title": "Document Title",
  "category": "reference|research_summary|test_pattern|code_example|architecture_decision|other",
  "document_type": "tool_selection_strategy|research_findings|best_practices|workflow|template",
  "purpose": "cost_optimization|research_guidance|decision_support|implementation_guide",
  "key_topics": ["topic1", "topic2", "topic3"],
  "version": "1.0|2.0|etc",
  "status": "active|deprecated",
  "priority": "critical|high|medium|low",
  "created_at": "ISO8601_timestamp",
  "updated_at": "ISO8601_timestamp",
  "source": "manual|research|code_analysis",
  "tags": ["tag1", "tag2"]
}
```

---

## Best Practices

### Content Organization:
1. **Start with summary** - First 1-2 sentences capture the essence
2. **Use clear section headers** - UPPERCASE with colons (e.g., `SECTION NAME:`)
3. **Keep sections focused** - One main idea per section
4. **Include keywords naturally** - Don't keyword stuff, embed naturally
5. **Add quick reference** - Tables, checklists, decision trees for fast lookup
6. **Provide examples** - Concrete examples improve understanding

### Metadata Best Practices:
1. **Use consistent categories** - reference, research_summary, test_pattern, etc.
2. **Include key topics** - Array of 3-7 main topics for filtering
3. **Version control** - Track versions (1.0, 2.0, etc.)
4. **Status tracking** - Mark deprecated documents
5. **Priority levels** - critical, high, medium, low
6. **Timestamps** - ISO8601 format for created_at/updated_at

### Search Optimization:
1. **Natural language** - Write in clear, natural language
2. **Explicit terms** - Use the exact terms people will search for
3. **Synonyms** - Include alternative terms in key_topics
4. **Context preservation** - Keep related information together
5. **Summary at start** - Helps embeddings capture main idea

---

## Example: Well-Formatted Document

```
TOOL SELECTION STRATEGY: Cost-Optimized Research Workflow

SUMMARY: Defines cost-optimized tool selection strategy for research tasks. Provides decision framework, credit costs, and escalation paths to minimize costs while maintaining quality.

HOW TO SEARCH & RETRIEVE:
[Search instructions]

CORE PRINCIPLE:
[Main principle]

AVAILABLE TOOLS & CREDIT COSTS:
[Tool list with costs]

DECISION FRAMEWORK:
[Decision tree]

WORKFLOW:
[Step-by-step process]

EXAMPLES:
[Concrete examples]

KEY RULES:
1. Rule 1
2. Rule 2
3. Rule 3

COST COMPARISON SUMMARY:
[Table format]

---

METADATA:
- doc_id: doc_48691f09bfb694f3
- category: reference
- document_type: tool_selection_strategy
- purpose: cost_optimized_research_workflow
- key_topics: ["tool selection", "cost optimization", "credit costs", "GPT-5 Mini", "Claude Sonnet"]
- version: 2.1
- status: active
- priority: critical
```

---

## Chunking Guidelines (if document is large)

### When to Chunk:
- Documents > 1000 tokens should be chunked
- Each chunk: 200-400 tokens (sweet spot: 300 tokens)
- Overlap: 10-30% between chunks (~50 tokens)

### Chunk Structure:
```
CHUNK 1: [Section Title]
[Content - 200-400 tokens]
- Include section header in chunk
- Keep semantically coherent
- Add summary at start if needed

CHUNK 2: [Next Section Title]
[Content - 200-400 tokens]
- Overlap with previous chunk if needed
- Maintain context
```

### Chunk Metadata:
```json
{
  "doc_id": "doc_123",
  "chunk_id": 1,
  "chunk_total": 5,
  "section": "Section Title",
  "section_hierarchy": ["Main Topic", "Section Title"],
  "chunk_offset": 0
}
```

---

## Quality Checklist

Before storing in Qdrant, verify:
- [ ] Document has clear title in UPPERCASE
- [ ] Summary (1-2 sentences) at the start
- [ ] Sections use UPPERCASE headers with colons
- [ ] Content is semantically coherent
- [ ] Keywords are naturally embedded
- [ ] Metadata is complete and accurate
- [ ] Key topics array has 3-7 relevant topics
- [ ] Version and status are set correctly
- [ ] Document is searchable (test with sample queries)
- [ ] No duplicate content (check existing documents)

---

## Search Query Examples

Documents formatted this way can be found with:
- `"tool selection strategy"` → Finds strategy documents
- `"cost optimization"` → Finds cost-related content
- `"GPT-5 Mini credits"` → Finds specific tool information
- `"decision framework"` → Finds decision-making guides
- `"workflow"` → Finds process documents

---

## Template Categories

### Reference Documents:
- Tool selection strategies
- Best practices
- Decision frameworks
- Quick reference guides

### Research Documents:
- Research findings
- Analysis results
- Comparison studies
- Technical investigations

### Code/Implementation:
- Code examples
- Implementation patterns
- Test strategies
- Architecture decisions

### Workflow Documents:
- Process guides
- Step-by-step instructions
- Checklists
- Templates

---

## Version Control

- **Version format:** `major.minor` (e.g., 1.0, 2.1)
- **Major version:** Significant changes, restructuring
- **Minor version:** Updates, corrections, additions
- **Status:** `active` (current) or `deprecated` (replaced)
- **Replacement:** If deprecated, include `replaced_by: doc_id`

---

## Final Notes

1. **Consistency is key** - Follow this template for all documents
2. **Test searchability** - Before storing, test with sample queries
3. **Update metadata** - Keep metadata current and accurate
4. **Remove duplicates** - Check for existing content before storing
5. **Mark deprecated** - Don't delete, mark as deprecated with replacement doc_id

