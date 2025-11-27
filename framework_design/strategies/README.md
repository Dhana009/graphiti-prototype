# Strategies Documentation

## Purpose
Contains strategies, workflows, and decision frameworks for AI-assisted development.

## Current Documents

### Tool Selection Strategy
- **File:** `TOOL_SELECTION_STRATEGY.md`
- **Version:** 2.1_with_search_guide
- **Status:** Active
- **Priority:** Critical

**Contents:**
- Cost-optimized tool selection framework
- Decision tree for question classification
- Escalation paths
- Credit cost comparisons
- Code Write Primary templates

## Key Principles
1. **Prompt Quality > Model Selection**
2. **Start with GPT-5 Mini** for most research
3. **Try 2-3 times** with improved prompts before escalating
4. **Use premium models** only for complex novel problems

## Cost Optimization
- GPT-5 Mini: ~6.54 credits/call
- Claude Sonnet: ~63.48 credits/call (9.7x more expensive)
- Strategy: 3 GPT-5 Mini calls (19.62 credits) < 1 Claude Sonnet call (63.48 credits)

## Storage
Stored in Qdrant as primary reference. Search with:
- `"tool selection strategy"`
- `"cost optimization"`
- `"which tool to use"`

