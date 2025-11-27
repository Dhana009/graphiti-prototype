# Gemini Code Implementation Guide - Relationship Querying & Management

## Research Date: 2025-11-25
**Tool:** Gemini Code Write Primary (Qwen 2.5 Coder 32B)
**Purpose:** Implementation guidance for fixing relationship querying and preventing duplicates

---

## Implementation Overview

Based on research findings, we need to:
1. Fix `get_entity_relationships` to query ALL relationship types (RELATIONSHIP, MENTIONS)
2. Implement proper MERGE pattern in `add_relationship` to prevent duplicates
3. Support querying relationships by direction (incoming, outgoing, both)
4. Return relationship type information in results

---

## 1. Updated `get_entity_relationships` Function

```python
import logging
from typing import List, Dict, Any, Optional
from neo4j import AsyncSession

logger = logging.getLogger(__name__)

async def get_entity_relationships(
    session: AsyncSession,
    entity_id: str,
    group_id: str,
    direction: str = "both"
) -> List[Dict[str, Any]]:
    """
    Retrieve relationships for a given entity, supporting multiple types and directions.

    Args:
        session: Neo4j async session.
        entity_id: The entity's ID.
        group_id: The entity's group ID.
        direction: "incoming", "outgoing", or "both" (default: "both").

    Returns:
        List of dicts with keys: 'rel_type' (label like "RELATIONSHIP"), 'rel_subtype' (property),
        'direction' ("incoming" or "outgoing"), 'connected_entity_id', 'connected_group_id',
        'rel_props' (full relationship properties dict).
    """
    if direction not in ["incoming", "outgoing", "both"]:
        raise ValueError("Direction must be 'incoming', 'outgoing', or 'both'.")
    
    query, params = build_relationship_query(entity_id, group_id, direction)
    
    try:
        result = await session.run(query, params)
        records = await result.fetchall()
        relationships = []
        for record in records:
            rel_type = record["rel_type"]
            rel_subtype = record["rel_subtype"]
            rel_direction = record["direction"]
            connected_entity_id = record["connected_entity_id"]
            connected_group_id = record["connected_group_id"]
            rel_props = dict(record["rel_props"])  # Full properties dict
            relationships.append({
                "rel_type": rel_type,
                "rel_subtype": rel_subtype,
                "direction": rel_direction,
                "connected_entity_id": connected_entity_id,
                "connected_group_id": connected_group_id,
                "rel_props": rel_props,
            })
        logger.info(f"Retrieved {len(relationships)} relationships for entity {entity_id} (direction: {direction}).")
        return relationships
    except Exception as e:
        logger.error(f"Error querying relationships for entity {entity_id}: {e}")
        raise
```

---

## 2. Updated `add_relationship` Function

```python
from typing import Dict, Any

async def add_relationship(
    session: AsyncSession,
    from_entity_id: str,
    to_entity_id: str,
    group_id: str,
    rel_type: str,
    rel_props: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add or update a relationship between two entities, preventing duplicates.

    Args:
        session: Neo4j async session.
        from_entity_id: Source entity's ID.
        to_entity_id: Target entity's ID.
        group_id: Group ID for entities and relationship.
        rel_type: Relationship label (e.g., "RELATIONSHIP" or "MENTIONS").
        rel_props: Optional dict of relationship properties (e.g., {"relationship_type": "colleague", "weight": 1.0}).
                   Must include 'relationship_type' if needed.
    """
    if rel_props is None:
        rel_props = {}
    
    # Ensure group_id is set on the relationship
    rel_props.setdefault("group_id", group_id)
    
    # Build dynamic SET clauses
    set_clauses = []
    match_set_clauses = []
    for key, value in rel_props.items():
        set_clauses.append(f"r.{key} = ${key}")
        match_set_clauses.append(f"r.{key} = ${key}")
    on_create_set = ", ".join(set_clauses) if set_clauses else ""
    on_match_set = ", ".join(match_set_clauses) if match_set_clauses else ""
    
    query = f"""
    MERGE (a:Entity {{entity_id: $from_entity_id, group_id: $group_id}})
    MERGE (b:Entity {{entity_id: $to_entity_id, group_id: $group_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    ON CREATE SET {on_create_set}
    ON MATCH SET {on_match_set}
    """
    
    params = {
        "from_entity_id": from_entity_id,
        "to_entity_id": to_entity_id,
        "group_id": group_id,
        **rel_props  # Unpack rel_props into params
    }
    
    try:
        await session.run(query, params)
        logger.info(f"Added/updated relationship ({rel_type}) from {from_entity_id} to {to_entity_id}.")
    except Exception as e:
        logger.error(f"Error adding relationship from {from_entity_id} to {to_entity_id}: {e}")
        raise
```

---

## 3. Helper Function: `build_relationship_query`

```python
from typing import Tuple

def build_relationship_query(entity_id: str, group_id: str, direction: str) -> Tuple[str, Dict[str, Any]]:
    """
    Build Cypher query for retrieving relationships based on direction.

    Returns:
        Tuple of (query_str, params_dict).
    """
    base_query = """
    MATCH (n:Entity {entity_id: $entity_id, group_id: $group_id})-[r:RELATIONSHIP|MENTIONS]-(connected:Entity)
    RETURN type(r) as rel_type, r.relationship_type as rel_subtype, 
           CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END as direction,
           connected.entity_id as connected_entity_id, connected.group_id as connected_group_id,
           properties(r) as rel_props
    """
    
    if direction == "outgoing":
        query = base_query.replace("-[r:RELATIONSHIP|MENTIONS]-", "-[r:RELATIONSHIP|MENTIONS]->")
    elif direction == "incoming":
        query = base_query.replace("(n:Entity {entity_id: $entity_id, group_id: $group_id})-[r:RELATIONSHIP|MENTIONS]-(connected:Entity)",
                                   "(connected:Entity)-[r:RELATIONSHIP|MENTIONS]->(n:Entity {entity_id: $entity_id, group_id: $group_id})")
    else:  # "both"
        query = base_query  # Undirected match
    
    params = {"entity_id": entity_id, "group_id": group_id}
    return query, params
```

---

## 4. Example Cypher Queries

### Querying Relationships (for `get_entity_relationships`)

**Outgoing:**
```cypher
MATCH (n:Entity {entity_id: $entity_id, group_id: $group_id})-[r:RELATIONSHIP|MENTIONS]->(connected:Entity)
RETURN type(r) as rel_type, 
       r.relationship_type as rel_subtype, 
       'outgoing' as direction,
       connected.entity_id as connected_entity_id, 
       connected.group_id as connected_group_id,
       properties(r) as rel_props
```

**Incoming:**
```cypher
MATCH (connected:Entity)-[r:RELATIONSHIP|MENTIONS]->(n:Entity {entity_id: $entity_id, group_id: $group_id})
RETURN type(r) as rel_type, 
       r.relationship_type as rel_subtype, 
       'incoming' as direction,
       connected.entity_id as connected_entity_id, 
       connected.group_id as connected_group_id,
       properties(r) as rel_props
```

**Both (Undirected):**
```cypher
MATCH (n:Entity {entity_id: $entity_id, group_id: $group_id})-[r:RELATIONSHIP|MENTIONS]-(connected:Entity)
RETURN type(r) as rel_type, 
       r.relationship_type as rel_subtype, 
       CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END as direction,
       connected.entity_id as connected_entity_id, 
       connected.group_id as connected_group_id,
       properties(r) as rel_props
```

### Adding/Updating Relationships (for `add_relationship`)

```cypher
MERGE (a:Entity {entity_id: $from_entity_id, group_id: $group_id})
MERGE (b:Entity {entity_id: $to_entity_id, group_id: $group_id})
MERGE (a)-[r:RELATIONSHIP]->(b)
ON CREATE SET r.group_id = $group_id, 
              r.relationship_type = $relationship_type,
              r.created_at = datetime()
ON MATCH SET r.group_id = $group_id, 
             r.relationship_type = $relationship_type,
             r.last_updated = datetime()
```

**Key Points:**
- MERGE nodes first, then relationship
- Never MERGE with relationship properties in pattern
- Use ON CREATE SET for initialization
- Use ON MATCH SET for updates

---

## 5. Key Design Decisions

### Relationship Types
- `:RELATIONSHIP` and `:MENTIONS` are Cypher relationship types (labels)
- `relationship_type` is a property (subtype, e.g., "colleague" or "mention")
- `group_id` is stored on both nodes and relationships

### Direction Support
- **"outgoing"**: Entity is the source
- **"incoming"**: Entity is the target
- **"both"**: Undirected (default for backward compatibility)

### Backward Compatibility
- Existing calls to `get_entity_relationships(entity_id, group_id)` will work (defaults to "both")
- For `add_relationship`, ensure callers provide `rel_type` as the label

### Performance
- Type alternation `[:RELATIONSHIP|MENTIONS]` is optimized per research
- Uses indexed properties (`entity_id`, `group_id`) for fast lookups

---

## 6. Implementation Notes

### Testing
- Test with sample data to ensure no duplicates
- Add a `:MENTIONS` relationship and verify `get_entity_relationships` returns it
- Test all three directions (incoming, outgoing, both)
- Verify MERGE prevents duplicate relationships

### Performance Considerations
- The type alternation pattern is optimized by Neo4j
- If you have many relationship types, consider indexing on relationship properties
- Monitor query performance with PROFILE

### Extensions
- If you need to query by specific `relationship_type` property, add filters:
  ```cypher
  WHERE r.relationship_type = $subtype
  ```
- Can extend to support additional relationship types by adding to the alternation pattern

---

## 7. Integration Points

### Where to Implement
1. **`graphiti_core/driver/neo4j_driver.py`**: Core driver methods
2. **`graffiti_mcp_implementation/src/relationships.py`**: MCP tool handlers
3. **`mcp_server/src/graphiti_mcp_server.py`**: HTTP MCP server handlers

### Current Code Locations to Update
- `get_entity_relationships` - likely in `relationships.py` or `neo4j_driver.py`
- `add_relationship` - likely in `relationships.py` or `neo4j_driver.py`
- MCP tool handlers that call these functions

---

## 8. Next Steps

1. ✅ Review current implementation
2. ✅ Identify exact file locations
3. ✅ Update `get_entity_relationships` with new query pattern
4. ✅ Update `add_relationship` with MERGE pattern
5. ✅ Add `build_relationship_query` helper
6. ✅ Update MCP tool handlers to use new functions
7. ✅ Test with sample data
8. ✅ Verify no duplicates are created
9. ✅ Test all relationship types are returned

---

**Status:** ✅ Implementation Guide Complete - Ready for Code Integration

