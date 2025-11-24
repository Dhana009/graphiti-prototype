"""Automatic entity/relationship extraction from unstructured text.

This module provides functions for extracting entities and relationships
from unstructured text using LLM and storing them in the knowledge graph.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI

from .database import DatabaseConnection
from .config import get_openai_config
from .validation import validate_group_id
from .entities import add_entity, update_entity, delete_entity, get_entity_by_id, EntityError
from .relationships import add_relationship, get_entity_relationships, RelationshipError
from .embeddings import generate_entity_embedding

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT_TEMPLATE = """Extract entities and relationships from the following text.

Return a JSON object with this exact structure:
{{
  "entities": [
    {{
      "entity_id": "unique_id_for_entity",
      "entity_type": "Type of entity (e.g., User, Module, Rule)",
      "name": "Human-readable name",
      "summary": "Brief description (optional)",
      "properties": {{"key": "value"}}  // Optional key-value properties
    }}
  ],
  "relationships": [
    {{
      "source_entity_id": "entity_id_of_source",
      "target_entity_id": "entity_id_of_target",
      "relationship_type": "Type of relationship (e.g., USES, DEPENDS_ON, WORKS_ON)",
      "fact": "Human-readable description of relationship (optional)",
      "properties": {{"key": "value"}}  // Optional key-value properties
    }}
  ]
}}

Guidelines:
- Extract all entities mentioned in the text
- Extract all relationships between entities
- Use clear, descriptive entity_id format (e.g., "user:john_doe", "module:auth")
- Use descriptive relationship types (e.g., USES, DEPENDS_ON, WORKS_ON, OWNS)
- Include summaries when helpful for understanding
- Only include properties that are explicitly mentioned in the text

Text to analyze:
{text}
"""


def _call_llm_for_extraction(text: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Call LLM to extract entities and relationships from text.

    Args:
        text: Unstructured text to extract from
        model: Optional LLM model name (defaults to config model)

    Returns:
        Dict[str, Any]: Extracted entities and relationships in structured format

    Raises:
        RuntimeError: If OpenAI API key is not configured
        ValueError: If LLM response is invalid JSON
        Exception: If LLM API call fails
    """
    openai_config = get_openai_config()
    if not openai_config.api_key:
        raise RuntimeError('OpenAI API key not configured. Set OPENAI_API_KEY environment variable.')

    model = model or openai_config.llm_model

    try:
        # Initialize OpenAI client with API key and optional organization
        client_kwargs = {"api_key": openai_config.api_key}
        if openai_config.organization:
            client_kwargs["organization"] = openai_config.organization
        client = OpenAI(**client_kwargs)
        
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(text=text)

        # Reasoning models (gpt-5 family, o1, o3) don't support temperature parameter
        # Standard models (gpt-4o-mini, etc.) support temperature
        is_reasoning_model = (
            model.startswith('gpt-5') or 
            model.startswith('o1') or 
            model.startswith('o3')
        )
        
        create_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a knowledge extraction assistant. Extract entities and relationships from text and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},  # Force JSON response
        }
        
        # Only add temperature for non-reasoning models
        # Reasoning models (gpt-5-nano, etc.) don't support temperature parameter
        # For standard models, use 0.0 for consistent extraction
        if not is_reasoning_model:
            # gpt-4o-mini doesn't support custom temperature, only default (1.0)
            if "gpt-4o-mini" not in model.lower():
                create_kwargs["temperature"] = 0.0
        
        response = client.chat.completions.create(**create_kwargs)

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")

        # Parse JSON response
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {content}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

        # Validate structure
        if not isinstance(result, dict):
            raise ValueError("LLM response must be a JSON object")
        if "entities" not in result:
            result["entities"] = []
        if "relationships" not in result:
            result["relationships"] = []

        if not isinstance(result["entities"], list):
            raise ValueError("entities must be a list")
        if not isinstance(result["relationships"], list):
            raise ValueError("relationships must be a list")

        logger.debug(f"LLM extracted {len(result['entities'])} entities and {len(result['relationships'])} relationships")
        return result

    except Exception as e:
        logger.error(f"Failed to extract entities/relationships from text: {e}")
        raise


def _deduplicate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate entities by entity_id.

    Args:
        entities: List of entity dictionaries

    Returns:
        List[Dict[str, Any]]: Deduplicated list of entities
    """
    seen = {}
    deduplicated = []

    for entity in entities:
        entity_id = entity.get("entity_id")
        if not entity_id:
            logger.warning("Skipping entity without entity_id")
            continue

        if entity_id not in seen:
            seen[entity_id] = entity
            deduplicated.append(entity)
        else:
            # Merge properties if duplicate (keep first, but merge properties)
            existing = seen[entity_id]
            if "properties" in entity and isinstance(entity["properties"], dict):
                if "properties" not in existing:
                    existing["properties"] = {}
                existing["properties"].update(entity["properties"])

    return deduplicated


async def add_memory(
    connection: DatabaseConnection,
    name: str,
    episode_body: str,
    source: str = "text",
    source_description: Optional[str] = None,
    group_id: Optional[str] = None,
    uuid: Optional[str] = None,
) -> Dict[str, Any]:
    """Add unstructured text and automatically extract entities/relationships.

    This function uses LLM to extract entities and relationships from unstructured
    text and stores them in the knowledge graph.

    Args:
        connection: DatabaseConnection instance (must be connected)
        name: Episode name/identifier (required)
        episode_body: Unstructured text content (required)
        source: Content type - "text", "json", or "message" (default: "text")
        source_description: Optional description of the source
        group_id: Optional group ID for multi-tenancy (defaults to 'default')
        uuid: Optional UUID for deduplication

    Returns:
        Dict[str, Any]: Result containing:
            - entities_created: Number of entities created
            - relationships_created: Number of relationships created
            - entities: List of created entity IDs
            - relationships: List of created relationship info

    Raises:
        ValueError: If validation fails
        RuntimeError: If connection is not initialized or OpenAI API key missing
        Exception: If extraction or storage fails

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await add_memory(
        ...         conn,
        ...         name="project_docs",
        ...         episode_body="John Doe works on the Auth Module.",
        ...         source="text",
        ...         group_id="my_group"
        ...     )
        >>> print(result['entities_created'])
        2
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    if not isinstance(name, str) or not name.strip():
        raise ValueError('name must be a non-empty string')
    if not isinstance(episode_body, str) or not episode_body.strip():
        raise ValueError('episode_body must be a non-empty string')
    if source not in ["text", "json", "message"]:
        raise ValueError(f'source must be one of: "text", "json", "message", got "{source}"')

    validated_group_id = validate_group_id(group_id)

    # Extract entities and relationships using LLM
    try:
        extracted = _call_llm_for_extraction(episode_body)
    except Exception as e:
        logger.error(f"Failed to extract entities/relationships: {e}")
        raise Exception(f"Failed to extract entities/relationships from text: {e}") from e

    # Deduplicate entities
    entities = _deduplicate_entities(extracted.get("entities", []))
    relationships = extracted.get("relationships", [])

    # Calculate and store content hash for change detection
    content_hash = _calculate_content_hash(episode_body)
    
    # Create entities
    entities_created = 0
    entities_created_list = []
    entities_failed = []
    first_entity_created = False

    for entity_data in entities:
        try:
            # Store content_hash on the first entity for this episode
            # This allows us to retrieve it later for comparison
            entity_properties = entity_data.get("properties", {})
            if uuid and not first_entity_created:
                entity_properties = entity_properties.copy() if entity_properties else {}
                entity_properties["episode_content_hash"] = content_hash
                entity_properties["episode_name"] = name
                first_entity_created = True
            
            entity = await add_entity(
                connection,
                entity_id=entity_data["entity_id"],
                entity_type=entity_data["entity_type"],
                name=entity_data["name"],
                properties=entity_properties,
                summary=entity_data.get("summary"),
                group_id=validated_group_id,
                episode_uuid=uuid if uuid else None,  # Track which episode created this entity
            )
            entities_created += 1
            entities_created_list.append(entity_data["entity_id"])
        except EntityError as e:
            # Entity might already exist (idempotent), log and continue
            logger.debug(f"Entity {entity_data.get('entity_id')} already exists or failed: {e}")
            entities_failed.append(entity_data.get("entity_id", "unknown"))

    # Create relationships
    relationships_created = 0
    relationships_created_list = []

    for rel_data in relationships:
        try:
            # Verify source and target entities exist
            source_id = rel_data.get("source_entity_id")
            target_id = rel_data.get("target_entity_id")

            if not source_id or not target_id:
                logger.warning(f"Skipping relationship with missing source or target: {rel_data}")
                continue

            # Check if entities exist (they should, since we just created them)
            try:
                await get_entity_by_id(connection, source_id, validated_group_id)
                await get_entity_by_id(connection, target_id, validated_group_id)
            except Exception:
                logger.warning(f"Skipping relationship: source or target entity not found")
                continue

            relationship = await add_relationship(
                connection,
                source_entity_id=source_id,
                target_entity_id=target_id,
                relationship_type=rel_data["relationship_type"],
                properties=rel_data.get("properties"),
                fact=rel_data.get("fact"),
                group_id=validated_group_id,
            )
            relationships_created += 1
            relationships_created_list.append({
                "source": source_id,
                "target": target_id,
                "type": rel_data["relationship_type"],
            })
        except (RelationshipError, EntityError) as e:
            # Relationship might already exist (idempotent), log and continue
            logger.debug(f"Relationship creation failed: {e}")

    logger.info(
        f"add_memory completed: {entities_created} entities, {relationships_created} relationships "
        f"(name: {name}, group: {validated_group_id})"
    )

    return {
        "entities_created": entities_created,
        "relationships_created": relationships_created,
        "entities": entities_created_list,
        "relationships": relationships_created_list,
        "entities_failed": entities_failed,
    }


def _calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 hash of content for change detection.

    Args:
        content: Text content to hash

    Returns:
        str: Hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _compare_entities(
    old_entities: List[Dict[str, Any]],
    new_entities: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Compare old and new entities to identify changes.

    Args:
        old_entities: List of existing entity dictionaries
        new_entities: List of new entity dictionaries

    Returns:
        Tuple containing:
            - added: Entities that are new (not in old)
            - removed: Entities that were removed (in old, not in new)
            - modified: Entities that exist in both but changed
    """
    old_by_id = {e.get("entity_id"): e for e in old_entities if e.get("entity_id")}
    new_by_id = {e.get("entity_id"): e for e in new_entities if e.get("entity_id")}

    old_ids = set(old_by_id.keys())
    new_ids = set(new_by_id.keys())

    added = [new_by_id[eid] for eid in new_ids - old_ids]
    removed = [old_by_id[eid] for eid in old_ids - new_ids]

    # Find modified entities (same ID but different content)
    modified = []
    for eid in old_ids & new_ids:
        old_entity = old_by_id[eid]
        new_entity = new_by_id[eid]

        # Compare key fields (name, summary, properties)
        if (old_entity.get("name") != new_entity.get("name") or
            old_entity.get("summary") != new_entity.get("summary") or
            old_entity.get("properties") != new_entity.get("properties")):
            modified.append(new_entity)

    return added, removed, modified


def _compare_relationships(
    old_relationships: List[Dict[str, Any]],
    new_relationships: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Compare old and new relationships to identify changes.

    Args:
        old_relationships: List of existing relationship dictionaries
        new_relationships: List of new relationship dictionaries

    Returns:
        Tuple containing:
            - added: Relationships that are new
            - removed: Relationships that were removed
            - modified: Relationships that exist in both but changed
    """
    # Create unique keys for relationships (source, target, type)
    def rel_key(rel: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            rel.get("source_entity_id", ""),
            rel.get("target_entity_id", ""),
            rel.get("relationship_type", ""),
        )

    old_by_key = {rel_key(r): r for r in old_relationships}
    new_by_key = {rel_key(r): r for r in new_relationships}

    old_keys = set(old_by_key.keys())
    new_keys = set(new_by_key.keys())

    added = [new_by_key[key] for key in new_keys - old_keys]
    removed = [old_by_key[key] for key in old_keys - new_keys]

    # Find modified relationships (same key but different properties/fact)
    modified = []
    for key in old_keys & new_keys:
        old_rel = old_by_key[key]
        new_rel = new_by_key[key]

        if (old_rel.get("fact") != new_rel.get("fact") or
            old_rel.get("properties") != new_rel.get("properties")):
            modified.append(new_rel)

    return added, removed, modified


async def _get_memory_metadata(
    connection: DatabaseConnection,
    uuid: str,
    group_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve memory/episode metadata by UUID.

    Args:
        connection: DatabaseConnection instance
        uuid: UUID of the memory/episode
        group_id: Group ID for multi-tenancy

    Returns:
        Dict with metadata (content_hash, entities, relationships) or None if not found
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    driver = connection.get_driver()
    async with driver.session(database=connection.database) as session:
        async def get_metadata_tx(tx):
            # Query for entities and relationships associated with this UUID
            # Also retrieve content_hash from the first entity
            # For now, we'll store UUID as a property on entities
            # In a full implementation, we'd have an Episode node
            query = """
            MATCH (e:Entity {group_id: $group_id})
            WHERE e.episode_uuid = $uuid AND (e._deleted IS NULL OR e._deleted = false)
            WITH e
            ORDER BY e.created_at ASC
            LIMIT 1
            RETURN e.entity_id as first_entity_id, e.episode_content_hash as content_hash
            """
            result = await tx.run(query, uuid=uuid, group_id=group_id)
            record = await result.single()
            
            if not record:
                return None, None
            
            content_hash = record.get('content_hash')
            
            # Get all entity IDs for this episode
            query_all = """
            MATCH (e:Entity {group_id: $group_id})
            WHERE e.episode_uuid = $uuid AND (e._deleted IS NULL OR e._deleted = false)
            RETURN collect(DISTINCT e.entity_id) as entity_ids
            """
            result_all = await tx.run(query_all, uuid=uuid, group_id=group_id)
            record_all = await result_all.single()
            entity_ids = record_all['entity_ids'] if record_all else []
            
            return entity_ids, content_hash

        entity_ids, content_hash = await session.execute_read(get_metadata_tx)

        if not entity_ids:
            return None

        # Get all entities and relationships for this episode
        entities = []
        relationships = []

        for entity_id in entity_ids:
            try:
                entity = await get_entity_by_id(connection, entity_id, group_id)
                # Remove episode metadata from properties for comparison
                entity_props = entity.get("properties", {}).copy()
                entity_props.pop("episode_content_hash", None)
                entity_props.pop("episode_name", None)
                entities.append({
                    "entity_id": entity["entity_id"],
                    "entity_type": entity["entity_type"],
                    "name": entity["name"],
                    "summary": entity.get("summary"),
                    "properties": entity_props,
                })
            except EntityError:
                continue

            # Get relationships for this entity
            try:
                rels = await get_entity_relationships(connection, entity_id, direction="both", group_id=group_id)
                for rel in rels:
                    # Avoid duplicates
                    rel_key = (rel["source_entity_id"], rel["target_entity_id"], rel["relationship_type"])
                    if not any(
                        (r["source_entity_id"], r["target_entity_id"], r["relationship_type"]) == rel_key
                        for r in relationships
                    ):
                        relationships.append({
                            "source_entity_id": rel["source_entity_id"],
                            "target_entity_id": rel["target_entity_id"],
                            "relationship_type": rel["relationship_type"],
                            "fact": rel.get("fact"),
                            "properties": rel.get("properties", {}),
                        })
            except Exception:
                continue

        return {
            "uuid": uuid,
            "entity_ids": entity_ids,
            "entities": entities,
            "relationships": relationships,
            "content_hash": content_hash,
        }


async def update_memory(
    connection: DatabaseConnection,
    uuid: str,
    episode_body: str,
    name: Optional[str] = None,
    source: str = "text",
    source_description: Optional[str] = None,
    update_strategy: str = "incremental",
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update existing memory/episode with new content.

    This function supports two update strategies:
    - "incremental": Only update what changed (recommended)
    - "replace": Replace all content (simpler but less efficient)

    Args:
        connection: DatabaseConnection instance (must be connected)
        uuid: UUID of the existing memory/episode (required)
        episode_body: New content (required)
        name: Optional updated name
        source: Content type - "text", "json", or "message" (default: "text")
        source_description: Optional description of the source
        update_strategy: "incremental" or "replace" (default: "incremental")
        group_id: Optional group ID for multi-tenancy (defaults to 'default')

    Returns:
        Dict[str, Any]: Result containing:
            - entities_added: Number of entities added
            - entities_updated: Number of entities updated
            - entities_removed: Number of entities removed (soft-deleted)
            - relationships_added: Number of relationships added
            - relationships_updated: Number of relationships updated
            - relationships_removed: Number of relationships removed

    Raises:
        ValueError: If validation fails
        RuntimeError: If connection is not initialized or memory not found
        Exception: If extraction or update fails

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await update_memory(
        ...         conn,
        ...         uuid="existing-uuid",
        ...         episode_body="Updated content",
        ...         update_strategy="incremental",
        ...         group_id="my_group"
        ...     )
        >>> print(result['entities_updated'])
        2
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    if not isinstance(uuid, str) or not uuid.strip():
        raise ValueError('uuid must be a non-empty string')
    if not isinstance(episode_body, str) or not episode_body.strip():
        raise ValueError('episode_body must be a non-empty string')
    if source not in ["text", "json", "message"]:
        raise ValueError(f'source must be one of: "text", "json", "message", got "{source}"')
    if update_strategy not in ["incremental", "replace"]:
        raise ValueError(f'update_strategy must be "incremental" or "replace", got "{update_strategy}"')

    validated_group_id = validate_group_id(group_id)

    # Get existing memory metadata
    existing_metadata = await _get_memory_metadata(connection, uuid, validated_group_id)
    if existing_metadata is None:
        raise ValueError(f"Memory with UUID '{uuid}' not found in group '{validated_group_id}'")

    # Calculate content hash
    new_content_hash = _calculate_content_hash(episode_body)
    
    # Check if content hash matches - if so, skip update (no changes)
    old_content_hash = existing_metadata.get("content_hash")
    if old_content_hash and old_content_hash == new_content_hash:
        logger.info(f"Content hash matches for UUID '{uuid}', skipping update (no changes)")
        return {
            "entities_added": 0,
            "entities_updated": 0,
            "entities_removed": 0,
            "relationships_added": 0,
            "relationships_updated": 0,
            "relationships_removed": 0,
        }

    # For replace strategy, just delete and re-add
    if update_strategy == "replace":
        # Soft delete all existing entities
        for entity_id in existing_metadata["entity_ids"]:
            try:
                await delete_entity(connection, entity_id, validated_group_id, hard=False)
            except Exception:
                pass  # Entity might already be deleted

        # Re-add memory (this will create new entities)
        return await add_memory(
            connection,
            name=name or f"updated_{uuid}",
            episode_body=episode_body,
            source=source,
            source_description=source_description,
            group_id=validated_group_id,
            uuid=uuid,
        )

    # Incremental strategy: compare and update only what changed
    # Extract new entities and relationships
    try:
        new_extracted = _call_llm_for_extraction(episode_body)
    except Exception as e:
        logger.error(f"Failed to extract entities/relationships: {e}")
        raise Exception(f"Failed to extract entities/relationships from text: {e}") from e

    new_entities = _deduplicate_entities(new_extracted.get("entities", []))
    new_relationships = new_extracted.get("relationships", [])

    old_entities = existing_metadata.get("entities", [])
    old_relationships = existing_metadata.get("relationships", [])

    # Compare to find changes
    entities_added, entities_removed, entities_modified = _compare_entities(old_entities, new_entities)
    rels_added, rels_removed, rels_modified = _compare_relationships(old_relationships, new_relationships)

    # Apply changes
    entities_added_count = 0
    entities_updated_count = 0
    entities_removed_count = 0
    relationships_added_count = 0
    relationships_updated_count = 0
    relationships_removed_count = 0

    # Add new entities
    for entity_data in entities_added:
        try:
            await add_entity(
                connection,
                entity_id=entity_data["entity_id"],
                entity_type=entity_data["entity_type"],
                name=entity_data["name"],
                properties=entity_data.get("properties"),
                summary=entity_data.get("summary"),
                group_id=validated_group_id,
                episode_uuid=uuid,  # Track which episode created this entity (uuid is required for update_memory)
            )
            entities_added_count += 1
        except EntityError:
            pass  # Entity might already exist

    # Update modified entities
    for entity_data in entities_modified:
        try:
            await update_entity(
                connection,
                entity_id=entity_data["entity_id"],
                name=entity_data.get("name"),
                properties=entity_data.get("properties"),
                summary=entity_data.get("summary"),
                group_id=validated_group_id,
            )
            entities_updated_count += 1
        except EntityError:
            pass

    # Soft delete removed entities
    for entity_data in entities_removed:
        try:
            await delete_entity(connection, entity_data["entity_id"], validated_group_id, hard=False)
            entities_removed_count += 1
        except EntityError:
            pass

    # Add new relationships
    for rel_data in rels_added:
        try:
            await add_relationship(
                connection,
                source_entity_id=rel_data["source_entity_id"],
                target_entity_id=rel_data["target_entity_id"],
                relationship_type=rel_data["relationship_type"],
                properties=rel_data.get("properties"),
                fact=rel_data.get("fact"),
                group_id=validated_group_id,
            )
            relationships_added_count += 1
        except RelationshipError:
            pass

    # Update modified relationships (delete and recreate)
    for rel_data in rels_modified:
        try:
            # For now, relationships are idempotent via MERGE, so updating means
            # deleting and recreating. In a full implementation, we'd have update_relationship.
            # For simplicity, we'll just recreate (MERGE handles it)
            await add_relationship(
                connection,
                source_entity_id=rel_data["source_entity_id"],
                target_entity_id=rel_data["target_entity_id"],
                relationship_type=rel_data["relationship_type"],
                properties=rel_data.get("properties"),
                fact=rel_data.get("fact"),
                group_id=validated_group_id,
            )
            relationships_updated_count += 1
        except RelationshipError:
            pass

    # Soft delete removed relationships
    # Note: We don't have soft delete for relationships yet, so we'll skip this for now
    # relationships_removed_count = len(rels_removed)

    logger.info(
        f"update_memory completed (uuid: {uuid}, strategy: {update_strategy}, group: {validated_group_id}): "
        f"{entities_added_count} added, {entities_updated_count} updated, {entities_removed_count} removed"
    )

    return {
        "entities_added": entities_added_count,
        "entities_updated": entities_updated_count,
        "entities_removed": entities_removed_count,
        "relationships_added": relationships_added_count,
        "relationships_updated": relationships_updated_count,
        "relationships_removed": relationships_removed_count,
    }

