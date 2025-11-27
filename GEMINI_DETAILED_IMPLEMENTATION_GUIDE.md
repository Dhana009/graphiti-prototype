# Gemini Detailed Implementation Guide - Advanced Coding Help

## Research Date: 2025-11-25
**Tool:** Gemini Code Write Primary (Qwen 2.5 Coder 32B) - Second Call
**Purpose:** Detailed implementation guidance for relationship label vs property distinction, query patterns, and MERGE strategies

---

## 1. Relationship Label vs Property - Clear Distinction

### Relationship Labels (Types)
- **What they are:** Core "types" of relationships in Neo4j (e.g., `:RELATIONSHIP`, `:MENTIONS`)
- **Purpose:** Define semantic category or structure of the relationship
- **Characteristics:**
  - Mandatory for relationships
  - Inherently indexed for fast traversal
  - Query syntax: `MATCH ()-[r:RELATIONSHIP]-()`
  - Think of them as "primary classifier"
  - Enable efficient graph traversals

### Relationship Properties
- **What they are:** Optional key-value attributes (e.g., `relationship_type: "USES"`, `group_id: 123`)
- **Purpose:** Store additional details or subtypes within a label
- **Characteristics:**
  - Not automatically indexed (must create explicitly)
  - Queried using WHERE clauses: `WHERE r.relationship_type = "USES"`
  - Flexible for dynamic data
  - Can be slower to filter without indexing

### When to Use Each

**Use Labels For:**
- Broad, semantic categorization
- Fast, structural queries (e.g., "all relationships of type `:MENTIONS`")
- Grouping relationships by purpose or origin

**Use Properties For:**
- Fine-grained details or subtypes
- Filtering within labels (e.g., `relationship_type: "USES"` within `:RELATIONSHIP`)
- Polymorphism - one label can represent multiple subtypes

### Your Architecture
- `:RELATIONSHIP` = catch-all for user-created links
- `:MENTIONS` = specific semantic type (e.g., for text mentions)
- `relationship_type` property = sub-classification (e.g., "USES" as a subtype of `:RELATIONSHIP`)

---

## 2. Cypher Query Patterns - Querying Both Labels with Property Filters

### Efficient Pattern: Type Alternation with Property Filters

**Basic Pattern:**
```cypher
MATCH ()-[r:RELATIONSHIP|MENTIONS]-()
WHERE r.relationship_type IN ["USES", "DEPENDS_ON"] 
  AND r.group_id = $tenantGroupId
RETURN type(r) AS label, r.relationship_type AS subtype, r
```

**Why This Works:**
- Uses label matching first (fast)
- Then applies property filtering
- Efficient because Neo4j optimizes for relationship types

### Alternative: UNION ALL for Complex Logic

**When to Use:**
- Different logic per label
- Need separate planning per branch

```cypher
MATCH ()-[r:RELATIONSHIP]-()
WHERE r.relationship_type IN ["USES", "DEPENDS_ON"] 
  AND r.group_id = $tenantGroupId
RETURN type(r) AS label, r.relationship_type AS subtype, r
UNION ALL
MATCH ()-[r:MENTIONS]-()
WHERE r.relationship_type IN ["USES", "DEPENDS_ON"] 
  AND r.group_id = $tenantGroupId
RETURN type(r) AS label, r.relationship_type AS subtype, r
```

**Performance Tip:**
- Use `|` operator when logic is the same (simpler and faster)
- Use UNION ALL when you need label-specific logic

### Query Strategy

1. **Query by label first** for broad, fast traversals
2. **Query by property** when filtering within labels
3. **Combine both** for hybrid queries
4. **Always filter `group_id`** early for multi-tenancy

---

## 3. MERGE Patterns - Preventing Duplicates

### General MERGE for `:RELATIONSHIP`

**Pattern:**
```cypher
MERGE (a:Entity {entity_id: $nodeIdA})-[r:RELATIONSHIP {relationship_type: $subtype, group_id: $tenantGroupId}]-(b:Entity {entity_id: $nodeIdB})
ON CREATE SET r.createdAt = timestamp()
```

**Why It Prevents Duplicates:**
- MERGE matches on full pattern (nodes, type, and properties)
- If a `:RELATIONSHIP` with same `relationship_type` and `group_id` exists, it reuses it
- No duplicate creation

### MERGE for `:MENTIONS`

**Pattern:**
```cypher
MERGE (a:Entity {entity_id: $nodeIdA})-[r:MENTIONS {relationship_type: $subtype, group_id: $tenantGroupId}]-(b:Entity {entity_id: $nodeIdB})
ON CREATE SET r.mentionedAt = timestamp()
```

**Key Points:**
- Type is part of the match (prevents cross-type duplicates)
- Properties ensure uniqueness within the type

### Preventing Duplicates Across Labels

**If you want to avoid creating `:MENTIONS` if `:RELATIONSHIP` already exists:**

```cypher
OPTIONAL MATCH (a:Entity {entity_id: $nodeIdA})-[existing:RELATIONSHIP|MENTIONS]-(b:Entity {entity_id: $nodeIdB})
WHERE existing.relationship_type = $subtype AND existing.group_id = $tenantGroupId
WITH a, b, CASE WHEN existing IS NULL THEN true ELSE false END AS canCreate
CALL apoc.do.when(canCreate, 
  'MERGE (a)-[r:MENTIONS {relationship_type: $subtype, group_id: $tenantGroupId}]-(b) RETURN r', 
  'RETURN existing AS r', 
  {a: a, b: b, subtype: $subtype, tenantGroupId: $tenantGroupId})
YIELD value
RETURN value.r
```

**Note:** Requires APOC plugin. For simpler cases, MERGE within desired type is sufficient.

### Best Practice for MERGE
- Always bind parameters (e.g., `$subtype`) to avoid injection
- Include `group_id` in MERGE to enforce multi-tenancy
- Test with small datasets to confirm no duplicates

---

## 4. Recommended Return Format

### Should You Return Both Label and Property?

**YES** - Especially in your architecture where:
- Labels convey semantic type (e.g., `:RELATIONSHIP` vs `:MENTIONS`)
- Properties convey subtype (e.g., "USES" vs "DEPENDS_ON")

### Recommended Format

```cypher
RETURN {
  label: type(r),              // e.g., "RELATIONSHIP"
  subtype: r.relationship_type, // e.g., "USES"
  group_id: r.group_id,
  relationship: r             // Full object for additional properties
} AS relationshipDetails
```

**Why This Works:**
- Distinguishes contexts easily
- A `:RELATIONSHIP` with `subtype: "USES"` = user-defined usage link
- A `:MENTIONS` with `subtype: "USES"` = mention in text
- Allows consumers to handle both appropriately

### Python Return Format

```python
{
    'relationship_label': 'RELATIONSHIP',      # From type(r)
    'relationship_type': 'USES',                # From r.relationship_type
    'group_id': 'main',
    'source_entity_id': 'entity:123',
    'target_entity_id': 'entity:456',
    'properties': {...},                        # Additional properties
    'fact': '...',                              # If present
    'created_at': 1234567890,
    't_valid': None,
    't_invalid': None
}
```

---

## 5. Performance Optimization Tips

### Structure Queries for Maximum Performance

1. **Prioritize labels in MATCH clauses**
   ```cypher
   MATCH ()-[r:RELATIONSHIP]-()  // Fast - uses relationship type index
   ```

2. **Apply property filters in WHERE clauses**
   ```cypher
   WHERE r.relationship_type IN ["USES", "DEPENDS_ON"]
     AND r.group_id = $tenantGroupId
   ```

3. **Use bind parameters** for caching
   ```cypher
   WHERE r.group_id = $group_id  // Good - parameterized
   ```

4. **Avoid full graph scans**
   ```cypher
   MATCH (a:Person)-[r:RELATIONSHIP]-(b:Company)  // Good - specific labels
   ```

5. **Use `|` operator** instead of UNION when possible
   ```cypher
   MATCH ()-[r:RELATIONSHIP|MENTIONS]-()  // Faster than UNION
   ```

6. **Limit results** with LIMIT and use SKIP for pagination

### Indexes on Relationship Properties

**Create indexes for frequently filtered properties:**

```cypher
CREATE INDEX rel_relationship_type_index FOR ()-[r:RELATIONSHIP]-() ON (r.relationship_type);
CREATE INDEX rel_group_id_index FOR ()-[r:RELATIONSHIP]-() ON (r.group_id);
CREATE INDEX mentions_relationship_type_index FOR ()-[r:MENTIONS]-() ON (r.relationship_type);
CREATE INDEX mentions_group_id_index FOR ()-[r:MENTIONS]-() ON (r.group_id);
```

**Why:**
- Enables fast lookups
- Without indexes, property filters can be slow (O(n) scans)
- Drop unused indexes to save space

**Check indexes:**
```cypher
SHOW INDEXES
```

### Other Optimization Tips

1. **Monitor with EXPLAIN PROFILE:**
   - Look for "NodeByLabelScan" or "RelationshipTypeScan" (good)
   - Avoid "AllNodesScan" (bad)

2. **Composite indexes** for multiple properties:
   ```cypher
   CREATE INDEX rel_composite_index FOR ()-[r:RELATIONSHIP]-() 
   ON (r.relationship_type, r.group_id);
   ```

3. **Use Neo4j Browser's query profiler** for analysis

4. **For large graphs:** Consider denormalization or APOC procedures

---

## 6. Complete Updated Function Implementations

### Updated `get_entity_relationships`

**Key Changes:**
- Uses type alternation: `[r:RELATIONSHIP|MENTIONS]`
- Returns both `relationship_label` (from `type(r)`) and `relationship_type` (property)
- Handles soft-deleted relationships
- Filters by `relationship_types` parameter (only for `:RELATIONSHIP`)
- Uses UNION ALL for "both" direction (more performant than OPTIONAL MATCH)

```python
async def get_entity_relationships(
    connection: DatabaseConnection,
    entity_id: str,
    direction: str = 'both',
    relationship_types: Optional[list[str]] = None,  # Filters only :RELATIONSHIP by property
    limit: Optional[int] = None,
    group_id: Optional[str] = None,
    include_deleted: bool = False,
) -> list[Dict[str, Any]]:
    """
    Retrieve relationships for an entity, supporting type alternation (:RELATIONSHIP|MENTIONS).
    Returns both relationship label (e.g., "RELATIONSHIP") and property (e.g., "USES").
    """
    # Validation (existing code)
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')
    
    validated_entity_id = validate_entity_id(entity_id)
    validated_group_id = validate_group_id(group_id)
    
    if direction not in ['incoming', 'outgoing', 'both']:
        raise ValueError(f"direction must be 'incoming', 'outgoing', or 'both', got '{direction}'")
    
    # Verify entity exists
    try:
        await get_entity_by_id(connection, validated_entity_id, validated_group_id)
    except EntityNotFoundError:
        raise EntityNotFoundError(
            f"Entity with ID '{validated_entity_id}' not found in group '{validated_group_id}'"
        )
    
    driver = connection.get_driver()
    
    async with driver.session(database=connection.database) as session:
        async def get_relationships_tx(tx):
            # Build WHERE clause
            where_parts = []
            if not include_deleted:
                where_parts.append("(r._deleted IS NULL OR r._deleted = false)")
            where_parts.append("r.group_id = $group_id")
            
            # Filter by relationship_types (only for :RELATIONSHIP)
            if relationship_types:
                where_parts.append(
                    "(type(r) = 'RELATIONSHIP' AND r.relationship_type IN $relationship_types)"
                )
            
            where_clause = " AND ".join(where_parts)
            
            # Build queries based on direction
            queries = []
            params = {
                'entity_id': validated_entity_id,
                'group_id': validated_group_id,
            }
            if relationship_types:
                params['relationship_types'] = relationship_types
            
            if direction in ('outgoing', 'both'):
                outgoing_query = f"""
                MATCH (e:Entity {{entity_id: $entity_id, group_id: $group_id}})
                      -[r:RELATIONSHIP|MENTIONS]->(target:Entity {{group_id: $group_id}})
                WHERE {where_clause}
                RETURN type(r) as relationship_label,
                       r.relationship_type as relationship_type,
                       r.group_id as group_id,
                       r.created_at as created_at,
                       r.fact as fact,
                       r.t_valid as t_valid,
                       r.t_invalid as t_invalid,
                       r._deleted as _deleted,
                       r.deleted_at as deleted_at,
                       startNode(r).entity_id as source_entity_id,
                       endNode(r).entity_id as target_entity_id,
                       r
                ORDER BY r.created_at
                """
                queries.append((outgoing_query, params))
            
            if direction in ('incoming', 'both'):
                incoming_query = f"""
                MATCH (source:Entity {{group_id: $group_id}})
                      -[r:RELATIONSHIP|MENTIONS]->(e:Entity {{entity_id: $entity_id, group_id: $group_id}})
                WHERE {where_clause}
                RETURN type(r) as relationship_label,
                       r.relationship_type as relationship_type,
                       r.group_id as group_id,
                       r.created_at as created_at,
                       r.fact as fact,
                       r.t_valid as t_valid,
                       r.t_invalid as t_invalid,
                       r._deleted as _deleted,
                       r.deleted_at as deleted_at,
                       startNode(r).entity_id as source_entity_id,
                       endNode(r).entity_id as target_entity_id,
                       r
                ORDER BY r.created_at
                """
                queries.append((incoming_query, params))
            
            # Execute queries and collect results
            all_records = []
            for query, query_params in queries:
                result = await tx.run(query, **query_params)
                records = [record async for record in result]
                all_records.extend(records)
            
            # Apply limit globally if specified
            if limit and len(all_records) > limit:
                all_records = all_records[:limit]
            
            return all_records
        
        try:
            records = await session.execute_read(get_relationships_tx)
            
            relationships = []
            for record in records:
                # Extract properties (excluding core fields)
                rel_properties = {}
                rel = record['r']
                for k, v in rel.items():
                    if k not in ['relationship_type', 'group_id', 'created_at', 'fact', 
                                't_valid', 't_invalid', '_deleted', 'deleted_at']:
                        rel_properties[k] = v
                
                relationship = {
                    'relationship_label': record['relationship_label'],  # NEW: Label from type(r)
                    'source_entity_id': record['source_entity_id'],
                    'target_entity_id': record['target_entity_id'],
                    'relationship_type': record['relationship_type'],  # Property (may be None for :MENTIONS)
                    'group_id': record['group_id'],
                    'created_at': record['created_at'],
                    'properties': rel_properties,
                }
                
                if record.get('fact') is not None:
                    relationship['fact'] = record['fact']
                if record.get('t_valid') is not None:
                    relationship['t_valid'] = record['t_valid']
                if record.get('t_invalid') is not None:
                    relationship['t_invalid'] = record['t_invalid']
                
                if include_deleted:
                    relationship['_deleted'] = record.get('_deleted')
                    relationship['deleted_at'] = record.get('deleted_at')
                
                relationships.append(relationship)
            
            logger.info(
                f"Retrieved {len(relationships)} relationships for entity {validated_entity_id} "
                f"(direction: {direction}, group: {validated_group_id})"
            )
            
            return relationships
        
        except Exception as e:
            logger.error(f"Error querying relationships for entity {validated_entity_id}: {e}")
            raise
```

### Updated `add_relationship`

**Key Changes:**
- MERGE nodes first, then relationship without properties in pattern
- Uses ON CREATE SET and ON MATCH SET for properties
- Uses `SET r += $rel_props` for incremental updates
- Proper error handling

```python
async def add_relationship(
    connection: DatabaseConnection,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,  # Property value for :RELATIONSHIP
    properties: Optional[Dict[str, Any]] = None,
    fact: Optional[str] = None,
    t_valid: Optional[datetime] = None,
    t_invalid: Optional[datetime] = None,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add or update a :RELATIONSHIP (not :MENTIONS) with proper MERGE to avoid duplicates.
    Merges nodes first, then relationship without properties in pattern.
    Sets properties incrementally.
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')
    
    # Validate inputs
    validated_source_id, validated_target_id, validated_type, validated_properties = validate_relationship_input(
        source_entity_id, target_entity_id, relationship_type, properties
    )
    validated_group_id = validate_group_id(group_id)
    
    # Validate that entities exist
    await validate_entities_exist(connection, validated_source_id, validated_target_id, validated_group_id)
    
    driver = connection.get_driver()
    
    # Prepare properties dict
    rel_props = {}
    rel_props['relationship_type'] = validated_type
    rel_props['group_id'] = validated_group_id
    rel_props['created_at'] = 'timestamp()'  # Will be evaluated by Neo4j
    
    if fact is not None:
        rel_props['fact'] = fact
    if t_valid is not None:
        rel_props['t_valid'] = t_valid.isoformat() if isinstance(t_valid, datetime) else t_valid
    if t_invalid is not None:
        rel_props['t_invalid'] = t_invalid.isoformat() if isinstance(t_invalid, datetime) else t_invalid
    if validated_properties:
        rel_props.update(validated_properties)
    
    async with driver.session(database=connection.database) as session:
        async def create_relationship_tx(tx):
            # Build SET clauses for ON CREATE and ON MATCH
            on_create_parts = []
            on_match_parts = []
            
            # Core properties (set on create, update on match)
            on_create_parts.append('r.relationship_type = $relationship_type')
            on_create_parts.append('r.group_id = $group_id')
            on_create_parts.append('r.created_at = timestamp()')
            
            on_match_parts.append('r.last_updated = timestamp()')  # Track updates
            
            # Optional properties
            if fact is not None:
                on_create_parts.append('r.fact = $fact')
                on_match_parts.append('r.fact = $fact')
            
            if t_valid is not None:
                on_create_parts.append('r.t_valid = $t_valid')
                on_match_parts.append('r.t_valid = $t_valid')
            
            if t_invalid is not None:
                on_create_parts.append('r.t_invalid = $t_invalid')
                on_match_parts.append('r.t_invalid = $t_invalid')
            
            # Dynamic properties (use += for incremental updates)
            if validated_properties:
                # Build property map for += operation
                prop_map = {}
                for key, value in validated_properties.items():
                    prop_map[key] = value
                on_create_parts.append('r += $dynamic_props')
                on_match_parts.append('r += $dynamic_props')
            
            on_create_set = ', '.join(on_create_parts) if on_create_parts else ''
            on_match_set = ', '.join(on_match_parts) if on_match_parts else ''
            
            # MERGE pattern: nodes first, then relationship without properties
            query = f"""
            MERGE (s:Entity {{entity_id: $source_id, group_id: $group_id}})
            MERGE (t:Entity {{entity_id: $target_id, group_id: $group_id}})
            MERGE (s)-[r:RELATIONSHIP]->(t)
            ON CREATE SET {on_create_set}
            ON MATCH SET {on_match_set}
            RETURN r.relationship_type as relationship_type,
                   r.group_id as group_id,
                   r.created_at as created_at,
                   r.fact as fact,
                   r.t_valid as t_valid,
                   r.t_invalid as t_invalid,
                   r
            """
            
            params = {
                'source_id': validated_source_id,
                'target_id': validated_target_id,
                'group_id': validated_group_id,
                'relationship_type': validated_type,
            }
            
            if fact is not None:
                params['fact'] = fact
            if t_valid is not None:
                params['t_valid'] = t_valid.isoformat() if isinstance(t_valid, datetime) else t_valid
            if t_invalid is not None:
                params['t_invalid'] = t_invalid.isoformat() if isinstance(t_invalid, datetime) else t_invalid
            if validated_properties:
                params['dynamic_props'] = validated_properties
            
            result = await tx.run(query, **params)
            return await result.single()
        
        try:
            record = await session.execute_write(create_relationship_tx)
            
            if record is None:
                raise RelationshipError('Failed to create relationship')
            
            # Extract properties (excluding core fields)
            relationship_properties = {}
            rel = record['r']
            for k, v in rel.items():
                if k not in ['relationship_type', 'group_id', 'created_at', 'fact', 
                            't_valid', 't_invalid', 'last_updated']:
                    relationship_properties[k] = v
            
            relationship = {
                'source_entity_id': validated_source_id,
                'target_entity_id': validated_target_id,
                'relationship_type': record['relationship_type'],
                'group_id': record['group_id'],
                'created_at': record['created_at'],
                'properties': relationship_properties,
            }
            
            if record.get('fact') is not None:
                relationship['fact'] = record['fact']
            if record.get('t_valid') is not None:
                relationship['t_valid'] = record['t_valid']
            if record.get('t_invalid') is not None:
                relationship['t_invalid'] = record['t_invalid']
            
            logger.info(
                f"Created/updated relationship: {validated_source_id} --[{validated_type}]--> {validated_target_id} (group: {validated_group_id})"
            )
            
            return relationship
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            raise RelationshipError(f"Failed to create relationship: {e}") from e
```

---

## 7. Error Handling Patterns

### Neo4j Exception Hierarchy

```python
from neo4j.exceptions import (
    ClientError,        # Query syntax errors, constraint violations
    TransientError,     # Temporary issues (deadlocks, connection problems)
    ServiceUnavailable, # Driver/connection issues
    DatabaseError       # Broader database errors
)
```

### Error Handling Best Practices

1. **ClientError:** Query syntax errors, constraint violations
   - Log and re-raise with user-friendly message
   - Check for specific error codes if needed

2. **TransientError:** Temporary issues
   - Implement retry logic with exponential backoff
   - Log warning and retry

3. **ServiceUnavailable:** Connection issues
   - Log error and raise
   - May need to reconnect

4. **General Exception:** Unexpected errors
   - Log full error details
   - Re-raise as appropriate exception type

### Example Error Handling

```python
try:
    result = await session.run(query, **params)
    return await result.single()
except ClientError as e:
    logger.error(f"Query error: {e}")
    if "already exists" in str(e):
        raise ValueError("Relationship or constraint conflict")
    raise
except TransientError as e:
    logger.warning(f"Transient error, retrying: {e}")
    # Implement retry logic here
    raise
except ServiceUnavailable as e:
    logger.error(f"Connection error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

---

## 8. Summary of Key Changes

### For `get_entity_relationships`:
1. ✅ Change `[r:RELATIONSHIP]` to `[r:RELATIONSHIP|MENTIONS]` (type alternation)
2. ✅ Return both `relationship_label` (from `type(r)`) and `relationship_type` (property)
3. ✅ Filter `relationship_types` only for `:RELATIONSHIP` (property exists)
4. ✅ Use UNION ALL approach for "both" direction (more performant)
5. ✅ Handle soft-deleted relationships with type alternation

### For `add_relationship`:
1. ✅ MERGE nodes first, then relationship without properties in pattern
2. ✅ Use ON CREATE SET and ON MATCH SET for properties
3. ✅ Use `SET r += $dynamic_props` for incremental updates
4. ✅ Proper error handling with Neo4j exception hierarchy
5. ✅ Track `last_updated` on match

### Additional Recommendations:
1. ✅ Create indexes on `relationship_type` and `group_id` properties
2. ✅ Use EXPLAIN PROFILE to monitor query performance
3. ✅ Return both label and property in results for clarity
4. ✅ Maintain backward compatibility with existing API

---

**Status:** ✅ **Complete Implementation Guide Ready**

**Next Steps:** Implement changes in `graffiti_mcp_implementation/src/relationships.py`

