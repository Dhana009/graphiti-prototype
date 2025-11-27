# Implementation Changes Needed - Based on Gemini Code Write Guidance

## Current Issues Identified

### 1. `get_entity_relationships` - Missing MENTIONS Relationships

**Current Code (lines 359, 382, 405-406):**
- Only queries `:RELATIONSHIP` type
- Missing `:MENTIONS` relationships

**Fix Required:**
- Change `[r:RELATIONSHIP]` to `[r:RELATIONSHIP|MENTIONS]` in all three direction queries
- This uses type alternation pattern (fastest per research)

### 2. `add_relationship` - MERGE Anti-Pattern Causing Duplicates

**Current Code (line 195):**
```cypher
MERGE (s)-[r:RELATIONSHIP {relationship_type: $relationship_type, group_id: $group_id}]->(t)
```

**Problem:**
- MERGE with properties in pattern causes duplicates
- If existing relationship lacks those properties, MERGE creates a new one

**Fix Required:**
- MERGE nodes first
- MERGE relationship without properties in pattern
- Use ON CREATE SET and ON MATCH SET for properties

---

## Implementation Plan

### Step 1: Fix `get_entity_relationships`
- Update outgoing query (line 359)
- Update incoming query (line 382)
- Update both query (lines 405-406)
- Add type alternation: `[r:RELATIONSHIP|MENTIONS]`

### Step 2: Fix `add_relationship`
- Change MERGE pattern to MERGE nodes first
- Remove properties from MERGE pattern
- Add ON CREATE SET and ON MATCH SET clauses
- Maintain backward compatibility

---

## Files to Modify

1. `graffiti_mcp_implementation/src/relationships.py`
   - `get_entity_relationships` function (lines 252-482)
   - `add_relationship` function (lines 80-249)

---

## Testing Requirements

1. Test that `get_entity_relationships` returns both RELATIONSHIP and MENTIONS types
2. Test that `add_relationship` doesn't create duplicates
3. Test all three directions (incoming, outgoing, both)
4. Verify backward compatibility

---

**Status:** Ready for Implementation

