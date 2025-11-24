"""Unit tests for memory content comparison functions.

These tests verify that content hash calculation and entity/relationship
comparison functions work correctly.
"""

import pytest
from src.memory import (
    _calculate_content_hash,
    _compare_entities,
    _compare_relationships,
)


class TestCalculateContentHash:
    """Tests for _calculate_content_hash function."""

    def test_calculate_content_hash_returns_hex_string(self):
        """Test that content hash returns a hexadecimal string."""
        content = "Test content"
        hash_value = _calculate_content_hash(content)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_calculate_content_hash_consistent(self):
        """Test that same content produces same hash."""
        content = "Test content"
        hash1 = _calculate_content_hash(content)
        hash2 = _calculate_content_hash(content)
        
        assert hash1 == hash2

    def test_calculate_content_hash_different_content(self):
        """Test that different content produces different hashes."""
        content1 = "Test content 1"
        content2 = "Test content 2"
        hash1 = _calculate_content_hash(content1)
        hash2 = _calculate_content_hash(content2)
        
        assert hash1 != hash2

    def test_calculate_content_hash_empty_string(self):
        """Test that empty string produces valid hash."""
        hash_value = _calculate_content_hash("")
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_calculate_content_hash_unicode(self):
        """Test that unicode content is handled correctly."""
        content = "Test content with émojis 🎉 and 中文"
        hash_value = _calculate_content_hash(content)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


class TestCompareEntities:
    """Tests for _compare_entities function."""

    def test_compare_entities_no_changes(self):
        """Test that identical entities produce no changes."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert added == []
        assert removed == []
        assert modified == []

    def test_compare_entities_added(self):
        """Test that new entities are identified as added."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"},
            {"entity_id": "user:2", "entity_type": "User", "name": "Jane Smith"}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert len(added) == 1
        assert added[0]["entity_id"] == "user:2"
        assert removed == []
        assert modified == []

    def test_compare_entities_removed(self):
        """Test that removed entities are identified."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"},
            {"entity_id": "user:2", "entity_type": "User", "name": "Jane Smith"}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert added == []
        assert len(removed) == 1
        assert removed[0]["entity_id"] == "user:2"
        assert modified == []

    def test_compare_entities_modified_name(self):
        """Test that entities with changed name are identified as modified."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Smith"}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert added == []
        assert removed == []
        assert len(modified) == 1
        assert modified[0]["entity_id"] == "user:1"
        assert modified[0]["name"] == "John Smith"

    def test_compare_entities_modified_summary(self):
        """Test that entities with changed summary are identified as modified."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe", "summary": "Engineer"}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe", "summary": "Senior Engineer"}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert added == []
        assert removed == []
        assert len(modified) == 1
        assert modified[0]["summary"] == "Senior Engineer"

    def test_compare_entities_modified_properties(self):
        """Test that entities with changed properties are identified as modified."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe", "properties": {"role": "dev"}}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe", "properties": {"role": "senior"}}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert added == []
        assert removed == []
        assert len(modified) == 1
        assert modified[0]["properties"]["role"] == "senior"

    def test_compare_entities_complex_changes(self):
        """Test complex scenario with added, removed, and modified entities."""
        old_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"},
            {"entity_id": "user:2", "entity_type": "User", "name": "Jane Smith"},
            {"entity_id": "user:3", "entity_type": "User", "name": "Bob Wilson"}
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Smith"},  # Modified
            {"entity_id": "user:2", "entity_type": "User", "name": "Jane Smith"},  # Unchanged
            {"entity_id": "user:4", "entity_type": "User", "name": "Alice Brown"}  # Added
            # user:3 removed
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        assert len(added) == 1
        assert added[0]["entity_id"] == "user:4"
        assert len(removed) == 1
        assert removed[0]["entity_id"] == "user:3"
        assert len(modified) == 1
        assert modified[0]["entity_id"] == "user:1"

    def test_compare_entities_empty_lists(self):
        """Test comparison with empty lists."""
        added, removed, modified = _compare_entities([], [])
        
        assert added == []
        assert removed == []
        assert modified == []

    def test_compare_entities_missing_entity_id(self):
        """Test that entities without entity_id are skipped."""
        old_entities = [
            {"entity_type": "User", "name": "John Doe"}  # Missing entity_id
        ]
        new_entities = [
            {"entity_id": "user:1", "entity_type": "User", "name": "John Doe"}
        ]
        
        added, removed, modified = _compare_entities(old_entities, new_entities)
        
        # Entity without entity_id should be ignored
        assert len(added) == 1
        assert added[0]["entity_id"] == "user:1"


class TestCompareRelationships:
    """Tests for _compare_relationships function."""

    def test_compare_relationships_no_changes(self):
        """Test that identical relationships produce no changes."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            }
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        assert added == []
        assert removed == []
        assert modified == []

    def test_compare_relationships_added(self):
        """Test that new relationships are identified as added."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            },
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:db",
                "relationship_type": "USES"
            }
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        assert len(added) == 1
        assert added[0]["source_entity_id"] == "user:1"
        assert added[0]["target_entity_id"] == "module:db"
        assert added[0]["relationship_type"] == "USES"
        assert removed == []
        assert modified == []

    def test_compare_relationships_removed(self):
        """Test that removed relationships are identified."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            },
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:db",
                "relationship_type": "USES"
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            }
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        assert added == []
        assert len(removed) == 1
        assert removed[0]["target_entity_id"] == "module:db"
        assert modified == []

    def test_compare_relationships_modified_fact(self):
        """Test that relationships with changed fact are identified as modified."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON",
                "fact": "John works on auth"
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON",
                "fact": "John is the lead on auth"
            }
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        assert added == []
        assert removed == []
        assert len(modified) == 1
        assert modified[0]["fact"] == "John is the lead on auth"

    def test_compare_relationships_modified_properties(self):
        """Test that relationships with changed properties are identified as modified."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON",
                "properties": {"since": "2024-01-01"}
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON",
                "properties": {"since": "2024-06-01"}
            }
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        assert added == []
        assert removed == []
        assert len(modified) == 1
        assert modified[0]["properties"]["since"] == "2024-06-01"

    def test_compare_relationships_complex_changes(self):
        """Test complex scenario with added, removed, and modified relationships."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON",
                "fact": "John works on auth"
            },
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:db",
                "relationship_type": "USES"
            },
            {
                "source_entity_id": "user:2",
                "target_entity_id": "module:api",
                "relationship_type": "WORKS_ON"
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON",
                "fact": "John leads auth"  # Modified
            },
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:db",
                "relationship_type": "USES"  # Unchanged
            },
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:cache",
                "relationship_type": "USES"  # Added
            }
            # user:2 -> module:api removed
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        assert len(added) == 1
        assert added[0]["target_entity_id"] == "module:cache"
        assert len(removed) == 1
        assert removed[0]["source_entity_id"] == "user:2"
        assert len(modified) == 1
        assert modified[0]["fact"] == "John leads auth"

    def test_compare_relationships_empty_lists(self):
        """Test comparison with empty lists."""
        added, removed, modified = _compare_relationships([], [])
        
        assert added == []
        assert removed == []
        assert modified == []

    def test_compare_relationships_same_key_different_type(self):
        """Test that relationships with same source/target but different type are separate."""
        old_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "WORKS_ON"
            }
        ]
        new_rels = [
            {
                "source_entity_id": "user:1",
                "target_entity_id": "module:auth",
                "relationship_type": "OWNS"  # Different type
            }
        ]
        
        added, removed, modified = _compare_relationships(old_rels, new_rels)
        
        # Different relationship type means different relationship
        assert len(added) == 1
        assert added[0]["relationship_type"] == "OWNS"
        assert len(removed) == 1
        assert removed[0]["relationship_type"] == "WORKS_ON"
        assert modified == []

