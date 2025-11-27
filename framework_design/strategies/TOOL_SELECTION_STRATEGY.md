# Tool Selection Strategy: Cost-Optimized Research Workflow

## How to Search & Retrieve This Document from Qdrant

**Quick Access:** This document is stored in Qdrant and can be retrieved instantly using semantic search.

### Search Queries That Work:
- `"tool selection strategy"` - Primary search term
- `"GPT-5 Mini credits"` - Find cost information
- `"cost optimization decision"` - Find decision framework
- `"which tool to use"` - Find tool selection guidance
- `"Claude Sonnet vs GPT-5 Mini"` - Find cost comparisons
- `"prompt quality model selection"` - Find core principles

### Document Metadata:
- **Document ID:** `doc_48691f09bfb694f3`
- **Version:** `2.0_cleaned`
- **Status:** `active`
- **Category:** `reference`
- **Priority:** `critical`

### Quick Decision Reference:
When you need to quickly decide which tool to use:
1. Search Qdrant with: `"tool selection"` or `"which tool"` or `"cost optimization"`
2. The clean version (2.0_cleaned) will be returned first
3. Check the "Decision Framework" section for quick answers
4. Use the "Cost Comparison Summary" table for credit costs

**Note:** Old duplicate versions are marked as `deprecated` - always use the active version (2.0_cleaned).

---

## Core Principle
**Prompt Quality > Model Selection.** With proper prompting, GPT-5 Mini (~6.54 credits) can match Claude Sonnet quality (~63.48 credits) for well-known topics. Use premium models intelligently for truly complex novel problems.

---

## Available Tools & Credit Costs

### Budget Tier (Simple Questions)
- **Budget GPT-4o-mini**: Simple definitions, basic explanations
- **Budget GPT-5-nano**: Ultra-cheap summarization
- **Budget Meta Llama**: Extreme budget fallback

### Standard Tier (Primary Choice)
- **GPT-5 Mini** (`mcp_gemini_call_research_primary`): **~6.54 credits/call** ⭐
  - Best value: Can match premium quality with proper prompting
  - Use for: Well-known topics, standard research, best practices
- **Gemini 2.5 Flash** (`mcp_gemini_call_research_backup`): **~6.51 credits/call**
  - Backup when GPT-5 Mini fails
- **GPT-4.1**: **~12.98 credits/call**
  - More capability than GPT-5 Mini, still cheaper than premium

### Premium Tier (Use Sparingly)
- **Claude Sonnet 3.7** (`mcp_gemini_call_claude_sonnet_model`): **~63.48 credits/call** ⚠️
  - 9.7x more expensive than GPT-5 Mini
  - Use for: Complex novel problems requiring deep reasoning
- **GPT-5 Thinking**: **~93.26 credits/call** ⚠️
  - 14x more expensive than GPT-5 Mini
  - Use for: Critical production decisions only
  - Note: Has timeout issues

### Code Generation
- **Grok Code Fast** (`mcp_gemini_call_code_write_primary`): **~1.59 credits/call**
  - Use after research for practical code examples

---

## Decision Framework

### Step 1: Classify Question Type

**Simple** → Budget GPT-4o-mini
- Definitions, basic facts, simple explanations

**Well-Known Topic** → GPT-5 Mini (try 2-3 times)
- TDD, design patterns, established best practices
- Standard research with existing knowledge base
- Pattern identification

**Complex Novel Problem** → GPT-5 Mini once, then evaluate
- Deep reasoning across multiple domains
- Novel architectural decisions
- Creative solutions beyond established patterns
- Critical production decisions

### Step 2: Smart Escalation Path

**For Well-Known Topics:**
1. GPT-5 Mini with good prompt (6.54 credits)
2. GPT-5 Mini with improved prompt (6.54 credits)
3. GPT-5 Mini with more context (6.54 credits)
4. GPT-4.1 (12.98 credits) - still cheaper than Claude Sonnet
5. Claude Sonnet (63.48 credits) - only if all above fail

**For Complex Novel Problems:**
1. GPT-5 Mini with detailed prompt (6.54 credits)
2. **If response lacks depth/insight** → Claude Sonnet (63.48 credits) ✅ Worth it
3. **If critical production decision** → GPT-5 Thinking (93.26 credits)

---

## Workflow

### For Each Research Question:

1. **Classify** → Simple / Well-Known / Complex Novel
2. **Start with appropriate tool** → Budget tier / GPT-5 Mini / GPT-5 Mini (once)
3. **Evaluate response quality**
   - Sufficient? → Store & Continue
   - Insufficient? → Improve prompt and retry (for well-known topics)
   - Lacks depth? → Escalate to premium (for complex problems)
4. **Generate code examples** → Grok Code Fast (~1.59 credits)
5. **Store results** → Qdrant with metadata

### Cost Optimization Checklist:
- [ ] Tried GPT-5 Mini first? (6.54 credits)
- [ ] Improved prompt and tried again? (6.54 credits)
- [ ] Added context and tried once more? (6.54 credits)
- [ ] Only then considered GPT-4.1? (12.98 credits)
- [ ] Only as last resort considered Claude Sonnet? (63.48 credits)

**Cost Reality:** 3 GPT-5 Mini calls (19.62 credits) < 1 Claude Sonnet call (63.48 credits)

---

## Examples

### Well-Known Topic (Use GPT-5 Mini)
**Q: "What are the most critical test-driven development principles that AI coding assistants must follow?"**
- **Type:** Well-known (TDD is extensively documented)
- **Tool:** GPT-5 Mini (6.54 credits) - try 2-3 times with improved prompts
- **Escalate to:** GPT-4.1 → Claude Sonnet only if needed

### Complex Novel Problem (Consider Premium)
**Q: "Design a novel testing strategy for a distributed system combining event-driven architecture, eventual consistency, and real-time analytics, while maintaining test determinism."**
- **Type:** Complex novel (requires deep reasoning, creative synthesis)
- **Tool:** Try GPT-5 Mini once (6.54 credits)
- **If lacks depth:** Claude Sonnet (63.48 credits) ✅ Worth it

---

## Key Rules

1. **Always start with GPT-5 Mini** for research questions (6.54 credits)
2. **Invest in prompt quality** - better prompt + GPT-5 Mini > average prompt + Claude Sonnet
3. **Try GPT-5 Mini 2-3 times** with improved prompts before escalating
4. **Use premium models intelligently** - only for complex novel problems that need deep reasoning
5. **Use budget tier** for simple definitions/facts
6. **Always generate code examples** after research (Grok Code Fast, 1.59 credits)
7. **Track credit usage** and adjust strategy based on actual costs

---

## Code Write Primary Templates

**Template 1: Pattern Implementation**
```
Based on the [principle/pattern] from the research, implement a [specific function/class] 
in [language] that demonstrates [specific behavior]. Include test cases that cover:
- [Edge case 1 from research]
- [Edge case 2 from research]
- [Pattern/principle from research]
```

**Template 2: Real-World Application**
```
Using the [TDD principle] discussed in the research, create a [real-world scenario] 
implementation with comprehensive tests. The tests should demonstrate:
- [Specific test structure from research]
- [Specific naming convention from research]
- [Specific edge case handling from research]
```

---

## Cost Comparison Summary

| Tool | Credits/Call | Use When |
|------|--------------|----------|
| GPT-5 Mini | 6.54 | Primary choice for most research |
| GPT-4.1 | 12.98 | More capability, still cost-effective |
| Claude Sonnet | 63.48 | Complex novel problems only |
| GPT-5 Thinking | 93.26 | Critical production decisions only |
| Grok Code Fast | 1.59 | Code examples after research |

**Savings Strategy:** Try GPT-5 Mini multiple times (19.62 credits for 3 calls) before using Claude Sonnet (63.48 credits for 1 call). Potential savings: ~43.86 credits per question.
