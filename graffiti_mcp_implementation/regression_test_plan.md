# Graffiti Graph MCP - Comprehensive Regression Test Plan

## Test Strategy
- **Goal**: Find all breaking points, edge cases, and potential failures
- **Approach**: Test each of 14 tools with:
  1. Happy path (valid inputs)
  2. Edge cases (boundary values, empty strings, nulls)
  3. Invalid inputs (wrong types, missing required fields)
  4. Error conditions (non-existent entities, duplicates)
  5. Stress testing (large payloads, many operations)

## Tools to Test (14 total)

1. `add_entity` - Create new entity
2. `add_relationship` - Create relationship between entities
3. `get_entity_by_id` - Retrieve entity by ID
4. `get_entities_by_type` - Get all entities of a type
5. `get_entity_relationships` - Get relationships for an entity
6. `search_nodes` - Semantic search for entities
7. `add_memory` - Add unstructured text with auto-extraction
8. `update_memory` - Update existing memory
9. `soft_delete_entity` - Soft delete an entity
10. `soft_delete_relationship` - Soft delete a relationship
11. `restore_entity` - Restore soft-deleted entity
12. `restore_relationship` - Restore soft-deleted relationship
13. `hard_delete_entity` - Permanently delete entity
14. `hard_delete_relationship` - Permanently delete relationship

## Test Categories

### Category 1: Input Validation
- Missing required fields
- Invalid field types
- Empty strings
- Very long strings
- Special characters
- SQL injection attempts
- XSS attempts

### Category 2: Business Logic
- Duplicate entities
- Non-existent entities
- Circular relationships
- Self-referential relationships
- Invalid relationship types

### Category 3: Edge Cases
- Maximum string lengths
- Unicode characters
- Very large numbers
- Negative numbers
- Zero values
- Null/undefined values

### Category 4: Multi-tenancy
- Group ID isolation
- Cross-group access attempts
- Reserved group IDs
- Invalid group IDs

### Category 5: State Management
- Soft delete → restore → hard delete flows
- Update deleted entities
- Query deleted entities
- Cascade deletions

### Category 6: Performance
- Large payloads
- Many concurrent operations
- Deep relationship chains
- Large search results

## Results Tracking

For each test:
- ✅ PASS - Works as expected
- ⚠️ ACCEPTABLE - Fails but error is handled gracefully
- ❌ BLOCKER - Critical failure that needs immediate fix

