#!/usr/bin/env python3
"""Comprehensive regression testing for all 14 Graffiti Graph MCP tools.

This script tests each tool with various scenarios to find breaking points.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import MCP tool handlers
from src.mcp_server import (
    _handle_add_entity, _handle_add_relationship, _handle_get_entity_by_id,
    _handle_get_entities_by_type, _handle_get_entity_relationships,
    _handle_search_nodes, _handle_add_memory, _handle_update_memory,
    _handle_soft_delete_entity, _handle_soft_delete_relationship,
    _handle_restore_entity, _handle_restore_relationship,
    _handle_hard_delete_entity, _handle_hard_delete_relationship
)
from src.database import DatabaseConnection, initialize_database
from src.config import get_neo4j_config


class TestResult:
    """Track test results."""
    def __init__(self, tool_name: str, test_name: str):
        self.tool_name = tool_name
        self.test_name = test_name
        self.status = "PENDING"
        self.error = None
        self.response = None
        self.is_blocker = False
        self.is_acceptable = False

    def __repr__(self):
        status_icon = {
            "PASS": "[OK]",
            "ACCEPTABLE": "[WARN]",
            "BLOCKER": "[FAIL]",
            "PENDING": "[...]"
        }.get(self.status, "[?]")
        return f"{status_icon} {self.tool_name}::{self.test_name}"


class RegressionTester:
    """Comprehensive regression tester for MCP tools."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.connection = None
        self.test_entities: List[str] = []
        self.test_relationships: List[Tuple[str, str, str]] = []
        
    async def setup(self):
        """Initialize database connection."""
        config = get_neo4j_config()
        self.connection = DatabaseConnection(config=config)
        await self.connection.__aenter__()
        await initialize_database(self.connection)
        
        # Clean up any leftover test data from previous runs
        try:
            async with self.connection.driver.session() as session:
                await session.run(
                    "MATCH (e:Entity {group_id: 'regression-test'}) DETACH DELETE e"
                )
        except:
            pass
        
        print("[SETUP] Database connection established and cleaned")
        
    async def teardown(self):
        """Clean up test data."""
        if self.connection:
            # Clean up test entities (try both soft and hard delete)
            for entity_id in self.test_entities:
                try:
                    from src.entities import hard_delete_entity, soft_delete_entity
                    # Try hard delete first
                    try:
                        await hard_delete_entity(self.connection, entity_id, group_id="regression-test")
                    except:
                        # If that fails, try soft delete then hard delete
                        try:
                            await soft_delete_entity(self.connection, entity_id, group_id="regression-test")
                            await hard_delete_entity(self.connection, entity_id, group_id="regression-test")
                        except:
                            pass
                except:
                    pass
            
            # Clean up all entities in regression-test group (nuclear option)
            try:
                async with self.connection.driver.session() as session:
                    await session.run(
                        "MATCH (e:Entity {group_id: 'regression-test'}) DETACH DELETE e"
                    )
            except:
                pass
            
            await self.connection.__aexit__(None, None, None)
            print("[CLEANUP] Test data cleaned up")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[Any, Any]:
        """Call an MCP tool and return response/error."""
        try:
            handler_map = {
                "add_entity": _handle_add_entity,
                "add_relationship": _handle_add_relationship,
                "get_entity_by_id": _handle_get_entity_by_id,
                "get_entities_by_type": _handle_get_entities_by_type,
                "get_entity_relationships": _handle_get_entity_relationships,
                "search_nodes": _handle_search_nodes,
                "add_memory": _handle_add_memory,
                "update_memory": _handle_update_memory,
                "soft_delete_entity": _handle_soft_delete_entity,
                "soft_delete_relationship": _handle_soft_delete_relationship,
                "restore_entity": _handle_restore_entity,
                "restore_relationship": _handle_restore_relationship,
                "hard_delete_entity": _handle_hard_delete_entity,
                "hard_delete_relationship": _handle_hard_delete_relationship,
            }
            
            handler = handler_map.get(tool_name)
            if not handler:
                return None, f"Unknown tool: {tool_name}"
            
            # Call handler with connection context
            result = await handler(self.connection, arguments)
            return result, None
            
        except Exception as e:
            return None, str(e)
    
    def record_result(self, tool_name: str, test_name: str, response: Any, error: Any, 
                     is_blocker: bool = False, is_acceptable: bool = False):
        """Record a test result."""
        result = TestResult(tool_name, test_name)
        if error:
            if is_blocker:
                result.status = "BLOCKER"
                result.is_blocker = True
            elif is_acceptable:
                result.status = "ACCEPTABLE"
                result.is_acceptable = True
            else:
                result.status = "BLOCKER"  # Default to blocker if not specified
                result.is_blocker = True
            result.error = str(error)
        else:
            result.status = "PASS"
            result.response = response
        self.results.append(result)
        print(f"  {result}")
    
    # ========== TOOL 1: add_entity ==========
    async def test_add_entity(self):
        """Test add_entity tool."""
        print("\n[TEST] add_entity")
        
        # Test 1.1: Happy path
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-001",
            "entity_type": "test",
            "name": "Test Entity",
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append("test-entity-001")
        self.record_result("add_entity", "1.1_happy_path", response, error)
        
        # Test 1.2: Missing required field (entity_id)
        response, error = await self.call_tool("add_entity", {
            "entity_type": "test",
            "name": "Test Entity"
        })
        self.record_result("add_entity", "1.2_missing_entity_id", response, error, 
                          is_acceptable=True)  # Should return validation error
        
        # Test 1.3: Missing required field (entity_type)
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-002",
            "name": "Test Entity"
        })
        self.record_result("add_entity", "1.3_missing_entity_type", response, error,
                          is_acceptable=True)
        
        # Test 1.4: Missing required field (name)
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-003",
            "entity_type": "test"
        })
        self.record_result("add_entity", "1.4_missing_name", response, error,
                          is_acceptable=True)
        
        # Test 1.5: Duplicate entity_id
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-001",
            "entity_type": "test",
            "name": "Duplicate Entity",
            "group_id": "regression-test"
        })
        self.record_result("add_entity", "1.5_duplicate_entity_id", response, error,
                          is_acceptable=True)  # Should return error about duplicate
        
        # Test 1.6: Empty string entity_id
        response, error = await self.call_tool("add_entity", {
            "entity_id": "",
            "entity_type": "test",
            "name": "Test Entity"
        })
        self.record_result("add_entity", "1.6_empty_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 1.7: Very long entity_id (1000 chars)
        long_id = "a" * 1000
        response, error = await self.call_tool("add_entity", {
            "entity_id": long_id,
            "entity_type": "test",
            "name": "Test Entity",
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append(long_id)
        self.record_result("add_entity", "1.7_very_long_entity_id", response, error)
        
        # Test 1.8: Special characters in entity_id
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-!@#$%^&*()",
            "entity_type": "test",
            "name": "Test Entity",
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append("test-entity-!@#$%^&*()")
        self.record_result("add_entity", "1.8_special_chars_entity_id", response, error)
        
        # Test 1.9: Unicode characters in name
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-unicode",
            "entity_type": "test",
            "name": "测试实体 🚀 émojis",
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append("test-entity-unicode")
        self.record_result("add_entity", "1.9_unicode_name", response, error)
        
        # Test 1.10: Very long name (10,000 chars)
        long_name = "A" * 10000
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-long-name",
            "entity_type": "test",
            "name": long_name,
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append("test-entity-long-name")
        self.record_result("add_entity", "1.10_very_long_name", response, error)
        
        # Test 1.11: Invalid group_id (reserved)
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-reserved-group",
            "entity_type": "test",
            "name": "Test Entity",
            "group_id": "default"
        })
        self.record_result("add_entity", "1.11_reserved_group_id", response, error,
                          is_acceptable=True)  # Should reject reserved group
        
        # Test 1.12: Properties with various types
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-props",
            "entity_type": "test",
            "name": "Test Entity with Properties",
            "group_id": "regression-test",
            "properties": {
                "string": "value",
                "number": 42,
                "float": 3.14,
                "boolean": True,
                "null": None,
                "array": [1, 2, 3],
                "nested": {"key": "value"}
            }
        })
        if not error:
            self.test_entities.append("test-entity-props")
        # Arrays and nested objects are not supported - this is expected validation
        self.record_result("add_entity", "1.12_complex_properties", response, error,
                          is_acceptable=True)  # Expected - only flat properties supported
        
        # Test 1.13: SQL injection attempt in name
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-sql-injection",
            "entity_type": "test",
            "name": "'; DROP TABLE entities; --",
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append("test-entity-sql-injection")
        self.record_result("add_entity", "1.13_sql_injection_name", response, error)
        
        # Test 1.14: XSS attempt in name
        response, error = await self.call_tool("add_entity", {
            "entity_id": "test-entity-xss",
            "entity_type": "test",
            "name": "<script>alert('XSS')</script>",
            "group_id": "regression-test"
        })
        if not error:
            self.test_entities.append("test-entity-xss")
        self.record_result("add_entity", "1.14_xss_name", response, error)
    
    # ========== TOOL 2: add_relationship ==========
    async def test_add_relationship(self):
        """Test add_relationship tool."""
        print("\n[TEST] add_relationship")
        
        # Setup: Create two entities for relationship testing
        await self.call_tool("add_entity", {
            "entity_id": "rel-source-001",
            "entity_type": "test",
            "name": "Source Entity",
            "group_id": "regression-test"
        })
        await self.call_tool("add_entity", {
            "entity_id": "rel-target-001",
            "entity_type": "test",
            "name": "Target Entity",
            "group_id": "regression-test"
        })
        self.test_entities.extend(["rel-source-001", "rel-target-001"])
        
        # Test 2.1: Happy path
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RELATED_TO",
            "group_id": "regression-test"
        })
        if not error:
            self.test_relationships.append(("rel-source-001", "rel-target-001", "RELATED_TO"))
        self.record_result("add_relationship", "2.1_happy_path", response, error)
        
        # Test 2.2: Missing source_entity_id
        response, error = await self.call_tool("add_relationship", {
            "target_entity_id": "rel-target-001",
            "relationship_type": "RELATED_TO",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.2_missing_source", response, error,
                          is_acceptable=True)
        
        # Test 2.3: Missing target_entity_id
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "relationship_type": "RELATED_TO",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.3_missing_target", response, error,
                          is_acceptable=True)
        
        # Test 2.4: Missing relationship_type
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.4_missing_relationship_type", response, error,
                          is_acceptable=True)
        
        # Test 2.5: Non-existent source entity
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "non-existent-source",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RELATED_TO",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.5_nonexistent_source", response, error,
                          is_acceptable=True)
        
        # Test 2.6: Non-existent target entity
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "non-existent-target",
            "relationship_type": "RELATED_TO",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.6_nonexistent_target", response, error,
                          is_acceptable=True)
        
        # Test 2.7: Self-referential relationship
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-source-001",
            "relationship_type": "RELATES_TO_SELF",
            "group_id": "regression-test"
        })
        if not error:
            self.test_relationships.append(("rel-source-001", "rel-source-001", "RELATES_TO_SELF"))
        self.record_result("add_relationship", "2.7_self_referential", response, error)
        
        # Test 2.8: Duplicate relationship
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RELATED_TO",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.8_duplicate_relationship", response, error,
                          is_acceptable=True)  # Should return error about duplicate
        
        # Test 2.9: Empty relationship_type
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.9_empty_relationship_type", response, error,
                          is_acceptable=True)
        
        # Test 2.10: Very long relationship_type
        long_type = "A" * 500
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": long_type,
            "group_id": "regression-test"
        })
        if not error:
            self.test_relationships.append(("rel-source-001", "rel-target-001", long_type))
        self.record_result("add_relationship", "2.10_very_long_relationship_type", response, error)
        
        # Test 2.11: Cross-group relationship attempt
        await self.call_tool("add_entity", {
            "entity_id": "cross-group-entity",
            "entity_type": "test",
            "name": "Cross Group Entity",
            "group_id": "other-group"
        })
        response, error = await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "cross-group-entity",
            "relationship_type": "CROSS_GROUP",
            "group_id": "regression-test"
        })
        self.record_result("add_relationship", "2.11_cross_group_relationship", response, error,
                          is_acceptable=True)  # Should fail due to group mismatch
    
    # ========== TOOL 3: get_entity_by_id ==========
    async def test_get_entity_by_id(self):
        """Test get_entity_by_id tool."""
        print("\n[TEST] get_entity_by_id")
        
        # Test 3.1: Happy path (existing entity)
        response, error = await self.call_tool("get_entity_by_id", {
            "entity_id": "test-entity-001",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_by_id", "3.1_happy_path", response, error)
        
        # Test 3.2: Non-existent entity
        response, error = await self.call_tool("get_entity_by_id", {
            "entity_id": "non-existent-entity-999",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_by_id", "3.2_nonexistent_entity", response, error,
                          is_acceptable=True)  # Should return error or null
        
        # Test 3.3: Missing entity_id
        response, error = await self.call_tool("get_entity_by_id", {
            "group_id": "regression-test"
        })
        self.record_result("get_entity_by_id", "3.3_missing_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 3.4: Empty entity_id
        response, error = await self.call_tool("get_entity_by_id", {
            "entity_id": "",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_by_id", "3.4_empty_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 3.5: Wrong group_id
        response, error = await self.call_tool("get_entity_by_id", {
            "entity_id": "test-entity-001",
            "group_id": "wrong-group"
        })
        self.record_result("get_entity_by_id", "3.5_wrong_group_id", response, error,
                          is_acceptable=True)  # Should return not found
        
        # Test 3.6: Include deleted entities
        # First soft-delete an entity
        await self.call_tool("soft_delete_entity", {
            "entity_id": "test-entity-001",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("get_entity_by_id", {
            "entity_id": "test-entity-001",
            "group_id": "regression-test",
            "include_deleted": True
        })
        self.record_result("get_entity_by_id", "3.6_include_deleted", response, error)
        # Restore it
        await self.call_tool("restore_entity", {
            "entity_id": "test-entity-001",
            "group_id": "regression-test"
        })
    
    # ========== TOOL 4: get_entities_by_type ==========
    async def test_get_entities_by_type(self):
        """Test get_entities_by_type tool."""
        print("\n[TEST] get_entities_by_type")
        
        # Test 4.1: Happy path
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "test",
            "group_id": "regression-test"
        })
        self.record_result("get_entities_by_type", "4.1_happy_path", response, error)
        
        # Test 4.2: Missing entity_type
        response, error = await self.call_tool("get_entities_by_type", {
            "group_id": "regression-test"
        })
        self.record_result("get_entities_by_type", "4.2_missing_entity_type", response, error,
                          is_acceptable=True)
        
        # Test 4.3: Non-existent entity_type
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "non-existent-type-999",
            "group_id": "regression-test"
        })
        self.record_result("get_entities_by_type", "4.3_nonexistent_type", response, error)
        # Should return empty list, not error
        
        # Test 4.4: With limit
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "test",
            "group_id": "regression-test",
            "limit": 5
        })
        self.record_result("get_entities_by_type", "4.4_with_limit", response, error)
        
        # Test 4.5: With offset
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "test",
            "group_id": "regression-test",
            "offset": 1,
            "limit": 5
        })
        self.record_result("get_entities_by_type", "4.5_with_offset", response, error)
        
        # Test 4.6: Very large limit
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "test",
            "group_id": "regression-test",
            "limit": 1000000
        })
        # Validation correctly rejects very large limits - this is expected
        self.record_result("get_entities_by_type", "4.6_very_large_limit", response, error,
                          is_acceptable=True)  # Expected - validation working correctly
        
        # Test 4.7: Negative limit
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "test",
            "group_id": "regression-test",
            "limit": -1
        })
        self.record_result("get_entities_by_type", "4.7_negative_limit", response, error,
                          is_acceptable=True)
        
        # Test 4.8: Negative offset
        response, error = await self.call_tool("get_entities_by_type", {
            "entity_type": "test",
            "group_id": "regression-test",
            "offset": -1
        })
        self.record_result("get_entities_by_type", "4.8_negative_offset", response, error,
                          is_acceptable=True)
    
    # ========== TOOL 5: get_entity_relationships ==========
    async def test_get_entity_relationships(self):
        """Test get_entity_relationships tool."""
        print("\n[TEST] get_entity_relationships")
        
        # Test 5.1: Happy path - outgoing
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "rel-source-001",
            "direction": "outgoing",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.1_happy_path_outgoing", response, error)
        
        # Test 5.2: Happy path - incoming
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "rel-target-001",
            "direction": "incoming",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.2_happy_path_incoming", response, error)
        
        # Test 5.3: Happy path - both
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "rel-source-001",
            "direction": "both",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.3_happy_path_both", response, error)
        
        # Test 5.4: Missing entity_id
        response, error = await self.call_tool("get_entity_relationships", {
            "direction": "outgoing",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.4_missing_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 5.5: Non-existent entity
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "non-existent-entity-999",
            "direction": "outgoing",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.5_nonexistent_entity", response, error,
                          is_acceptable=True)
        
        # Test 5.6: Invalid direction
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "rel-source-001",
            "direction": "invalid-direction",
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.6_invalid_direction", response, error,
                          is_acceptable=True)
        
        # Test 5.7: Filter by relationship_type
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "rel-source-001",
            "direction": "outgoing",
            "relationship_types": ["RELATED_TO"],
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.7_filter_by_type", response, error)
        
        # Test 5.8: Include deleted relationships
        # First create and soft-delete a relationship
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "TEMPORARY_REL",
            "group_id": "regression-test"
        })
        await self.call_tool("soft_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "TEMPORARY_REL",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("get_entity_relationships", {
            "entity_id": "rel-source-001",
            "direction": "outgoing",
            "include_deleted": True,
            "group_id": "regression-test"
        })
        self.record_result("get_entity_relationships", "5.8_include_deleted", response, error)
    
    # ========== TOOL 6: search_nodes ==========
    async def test_search_nodes(self):
        """Test search_nodes tool."""
        print("\n[TEST] search_nodes")
        
        # Test 6.1: Happy path
        response, error = await self.call_tool("search_nodes", {
            "query": "test entity",
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.1_happy_path", response, error)
        
        # Test 6.2: Missing query
        response, error = await self.call_tool("search_nodes", {
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.2_missing_query", response, error,
                          is_acceptable=True)
        
        # Test 6.3: Empty query
        response, error = await self.call_tool("search_nodes", {
            "query": "",
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.3_empty_query", response, error,
                          is_acceptable=True)
        
        # Test 6.4: Very long query
        long_query = "test " * 1000
        response, error = await self.call_tool("search_nodes", {
            "query": long_query,
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.4_very_long_query", response, error)
        
        # Test 6.5: With max_nodes limit
        response, error = await self.call_tool("search_nodes", {
            "query": "test",
            "max_nodes": 5,
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.5_with_max_nodes", response, error)
        
        # Test 6.6: Very large max_nodes
        response, error = await self.call_tool("search_nodes", {
            "query": "test",
            "max_nodes": 10000,
            "group_id": "regression-test"
        })
        # Validation correctly rejects very large max_nodes - this is expected
        self.record_result("search_nodes", "6.6_very_large_max_nodes", response, error,
                          is_acceptable=True)  # Expected - validation working correctly
        
        # Test 6.7: Negative max_nodes
        response, error = await self.call_tool("search_nodes", {
            "query": "test",
            "max_nodes": -1,
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.7_negative_max_nodes", response, error,
                          is_acceptable=True)
        
        # Test 6.8: Filter by entity_types
        response, error = await self.call_tool("search_nodes", {
            "query": "test",
            "entity_types": ["test"],
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.8_filter_by_entity_types", response, error)
        
        # Test 6.9: Unicode query
        response, error = await self.call_tool("search_nodes", {
            "query": "测试 实体",
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.9_unicode_query", response, error)
        
        # Test 6.10: Special characters in query
        response, error = await self.call_tool("search_nodes", {
            "query": "test !@#$%^&*() query",
            "group_id": "regression-test"
        })
        self.record_result("search_nodes", "6.10_special_chars_query", response, error)
    
    # ========== TOOL 7: add_memory ==========
    async def test_add_memory(self):
        """Test add_memory tool."""
        print("\n[TEST] add_memory")
        
        # Test 7.1: Happy path
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-001",
            "episode_body": "This is a test memory about a person named John who works at a company called Acme Corp.",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.1_happy_path", response, error)
        
        # Test 7.2: Missing name
        response, error = await self.call_tool("add_memory", {
            "episode_body": "Test memory without name",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.2_missing_name", response, error,
                          is_acceptable=True)
        
        # Test 7.3: Missing episode_body
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-002",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.3_missing_episode_body", response, error,
                          is_acceptable=True)
        
        # Test 7.4: Empty episode_body
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-003",
            "episode_body": "",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.4_empty_episode_body", response, error,
                          is_acceptable=True)
        
        # Test 7.5: Very long episode_body
        long_body = "This is a test. " * 10000
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-long",
            "episode_body": long_body,
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.5_very_long_episode_body", response, error)
        
        # Test 7.6: Duplicate UUID
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-001",
            "episode_body": "Duplicate memory",
            "uuid": response.get("uuid") if response and isinstance(response, dict) else "test-uuid-001",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.6_duplicate_uuid", response, error,
                          is_acceptable=True)  # Should handle duplicate gracefully
        
        # Test 7.7: With source type
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-source",
            "episode_body": "Test memory with source type",
            "source": "text",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.7_with_source_type", response, error)
        
        # Test 7.8: Unicode in episode_body
        response, error = await self.call_tool("add_memory", {
            "name": "test-memory-unicode",
            "episode_body": "这是一个测试记忆。包含中文和emoji 🚀",
            "group_id": "regression-test"
        })
        self.record_result("add_memory", "7.8_unicode_episode_body", response, error)
    
    # ========== TOOL 8: update_memory ==========
    async def test_update_memory(self):
        """Test update_memory tool."""
        print("\n[TEST] update_memory")
        
        # Setup: Create a memory first
        create_response, _ = await self.call_tool("add_memory", {
            "name": "test-memory-update",
            "episode_body": "Original memory content",
            "group_id": "regression-test"
        })
        uuid = create_response.get("uuid") if create_response and isinstance(create_response, dict) else None
        
        # Test 8.1: Happy path
        if uuid:
            response, error = await self.call_tool("update_memory", {
                "uuid": uuid,
                "episode_body": "Updated memory content",
                "group_id": "regression-test"
            })
            self.record_result("update_memory", "8.1_happy_path", response, error)
        
        # Test 8.2: Missing uuid
        response, error = await self.call_tool("update_memory", {
            "episode_body": "Updated content",
            "group_id": "regression-test"
        })
        self.record_result("update_memory", "8.2_missing_uuid", response, error,
                          is_acceptable=True)
        
        # Test 8.3: Missing episode_body
        if uuid:
            response, error = await self.call_tool("update_memory", {
                "uuid": uuid,
                "group_id": "regression-test"
            })
            self.record_result("update_memory", "8.3_missing_episode_body", response, error,
                              is_acceptable=True)
        
        # Test 8.4: Non-existent uuid
        response, error = await self.call_tool("update_memory", {
            "uuid": "non-existent-uuid-999",
            "episode_body": "Updated content",
            "group_id": "regression-test"
        })
        self.record_result("update_memory", "8.4_nonexistent_uuid", response, error,
                          is_acceptable=True)
        
        # Test 8.5: Same content (should skip update)
        if uuid:
            response, error = await self.call_tool("update_memory", {
                "uuid": uuid,
                "episode_body": "Updated memory content",  # Same as after 8.1
                "group_id": "regression-test"
            })
            self.record_result("update_memory", "8.5_same_content", response, error)
        
        # Test 8.6: With update_strategy incremental
        if uuid:
            response, error = await self.call_tool("update_memory", {
                "uuid": uuid,
                "episode_body": "New incremental update",
                "update_strategy": "incremental",
                "group_id": "regression-test"
            })
            self.record_result("update_memory", "8.6_incremental_strategy", response, error)
        
        # Test 8.7: With update_strategy replace
        if uuid:
            response, error = await self.call_tool("update_memory", {
                "uuid": uuid,
                "episode_body": "New replace update",
                "update_strategy": "replace",
                "group_id": "regression-test"
            })
            self.record_result("update_memory", "8.7_replace_strategy", response, error)
    
    # ========== TOOL 9: soft_delete_entity ==========
    async def test_soft_delete_entity(self):
        """Test soft_delete_entity tool."""
        print("\n[TEST] soft_delete_entity")
        
        # Setup: Create entity for deletion
        await self.call_tool("add_entity", {
            "entity_id": "soft-delete-test",
            "entity_type": "test",
            "name": "Entity for Soft Delete",
            "group_id": "regression-test"
        })
        self.test_entities.append("soft-delete-test")
        
        # Test 9.1: Happy path
        response, error = await self.call_tool("soft_delete_entity", {
            "entity_id": "soft-delete-test",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_entity", "9.1_happy_path", response, error)
        
        # Test 9.2: Missing entity_id
        response, error = await self.call_tool("soft_delete_entity", {
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_entity", "9.2_missing_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 9.3: Non-existent entity
        response, error = await self.call_tool("soft_delete_entity", {
            "entity_id": "non-existent-entity-999",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_entity", "9.3_nonexistent_entity", response, error,
                          is_acceptable=True)
        
        # Test 9.4: Already soft-deleted entity
        response, error = await self.call_tool("soft_delete_entity", {
            "entity_id": "soft-delete-test",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_entity", "9.4_already_deleted", response, error,
                          is_acceptable=True)  # Should be idempotent
        
        # Test 9.5: Wrong group_id
        await self.call_tool("restore_entity", {
            "entity_id": "soft-delete-test",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("soft_delete_entity", {
            "entity_id": "soft-delete-test",
            "group_id": "wrong-group"
        })
        self.record_result("soft_delete_entity", "9.5_wrong_group_id", response, error,
                          is_acceptable=True)
    
    # ========== TOOL 10: soft_delete_relationship ==========
    async def test_soft_delete_relationship(self):
        """Test soft_delete_relationship tool."""
        print("\n[TEST] soft_delete_relationship")
        
        # Setup: Create relationship for deletion
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_DELETE_TEST",
            "group_id": "regression-test"
        })
        
        # Test 10.1: Happy path
        response, error = await self.call_tool("soft_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_DELETE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_relationship", "10.1_happy_path", response, error)
        
        # Test 10.2: Missing source_entity_id
        response, error = await self.call_tool("soft_delete_relationship", {
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_DELETE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_relationship", "10.2_missing_source", response, error,
                          is_acceptable=True)
        
        # Test 10.3: Non-existent relationship
        response, error = await self.call_tool("soft_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "NON_EXISTENT_REL",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_relationship", "10.3_nonexistent_relationship", response, error,
                          is_acceptable=True)
        
        # Test 10.4: Already soft-deleted relationship
        response, error = await self.call_tool("soft_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_DELETE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("soft_delete_relationship", "10.4_already_deleted", response, error,
                          is_acceptable=True)  # Should be idempotent
    
    # ========== TOOL 11: restore_entity ==========
    async def test_restore_entity(self):
        """Test restore_entity tool."""
        print("\n[TEST] restore_entity")
        
        # Setup: Create and soft-delete entity
        await self.call_tool("add_entity", {
            "entity_id": "restore-test-entity",
            "entity_type": "test",
            "name": "Entity for Restore Test",
            "group_id": "regression-test"
        })
        self.test_entities.append("restore-test-entity")
        await self.call_tool("soft_delete_entity", {
            "entity_id": "restore-test-entity",
            "group_id": "regression-test"
        })
        
        # Test 11.1: Happy path
        response, error = await self.call_tool("restore_entity", {
            "entity_id": "restore-test-entity",
            "group_id": "regression-test"
        })
        self.record_result("restore_entity", "11.1_happy_path", response, error)
        
        # Test 11.2: Missing entity_id
        response, error = await self.call_tool("restore_entity", {
            "group_id": "regression-test"
        })
        self.record_result("restore_entity", "11.2_missing_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 11.3: Non-existent entity
        response, error = await self.call_tool("restore_entity", {
            "entity_id": "non-existent-entity-999",
            "group_id": "regression-test"
        })
        self.record_result("restore_entity", "11.3_nonexistent_entity", response, error,
                          is_acceptable=True)
        
        # Test 11.4: Already restored entity (not deleted)
        response, error = await self.call_tool("restore_entity", {
            "entity_id": "restore-test-entity",
            "group_id": "regression-test"
        })
        self.record_result("restore_entity", "11.4_already_restored", response, error,
                          is_acceptable=True)  # Should be idempotent
        
        # Test 11.5: Restore hard-deleted entity (should fail)
        # First hard-delete an entity
        await self.call_tool("add_entity", {
            "entity_id": "hard-deleted-entity",
            "entity_type": "test",
            "name": "Entity to Hard Delete",
            "group_id": "regression-test"
        })
        await self.call_tool("hard_delete_entity", {
            "entity_id": "hard-deleted-entity",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("restore_entity", {
            "entity_id": "hard-deleted-entity",
            "group_id": "regression-test"
        })
        self.record_result("restore_entity", "11.5_restore_hard_deleted", response, error,
                          is_acceptable=True)  # Should fail - can't restore hard-deleted
    
    # ========== TOOL 12: restore_relationship ==========
    async def test_restore_relationship(self):
        """Test restore_relationship tool."""
        print("\n[TEST] restore_relationship")
        
        # Setup: Create and soft-delete relationship
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RESTORE_TEST",
            "group_id": "regression-test"
        })
        await self.call_tool("soft_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RESTORE_TEST",
            "group_id": "regression-test"
        })
        
        # Test 12.1: Happy path
        response, error = await self.call_tool("restore_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RESTORE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("restore_relationship", "12.1_happy_path", response, error)
        
        # Test 12.2: Missing source_entity_id
        response, error = await self.call_tool("restore_relationship", {
            "target_entity_id": "rel-target-001",
            "relationship_type": "RESTORE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("restore_relationship", "12.2_missing_source", response, error,
                          is_acceptable=True)
        
        # Test 12.3: Non-existent relationship
        response, error = await self.call_tool("restore_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "NON_EXISTENT_REL",
            "group_id": "regression-test"
        })
        self.record_result("restore_relationship", "12.3_nonexistent_relationship", response, error,
                          is_acceptable=True)
        
        # Test 12.4: Already restored relationship
        response, error = await self.call_tool("restore_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "RESTORE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("restore_relationship", "12.4_already_restored", response, error,
                          is_acceptable=True)  # Should be idempotent
        
        # Test 12.5: Restore hard-deleted relationship (should fail)
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_REL",
            "group_id": "regression-test"
        })
        await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_REL",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("restore_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_REL",
            "group_id": "regression-test"
        })
        self.record_result("restore_relationship", "12.5_restore_hard_deleted", response, error,
                          is_acceptable=True)  # Should fail - can't restore hard-deleted
    
    # ========== TOOL 13: hard_delete_entity ==========
    async def test_hard_delete_entity(self):
        """Test hard_delete_entity tool."""
        print("\n[TEST] hard_delete_entity")
        
        # Setup: Create entity for deletion
        await self.call_tool("add_entity", {
            "entity_id": "hard-delete-test",
            "entity_type": "test",
            "name": "Entity for Hard Delete",
            "group_id": "regression-test"
        })
        
        # Test 13.1: Happy path
        response, error = await self.call_tool("hard_delete_entity", {
            "entity_id": "hard-delete-test",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_entity", "13.1_happy_path", response, error)
        
        # Test 13.2: Missing entity_id
        response, error = await self.call_tool("hard_delete_entity", {
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_entity", "13.2_missing_entity_id", response, error,
                          is_acceptable=True)
        
        # Test 13.3: Non-existent entity
        response, error = await self.call_tool("hard_delete_entity", {
            "entity_id": "non-existent-entity-999",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_entity", "13.3_nonexistent_entity", response, error,
                          is_acceptable=True)
        
        # Test 13.4: Already hard-deleted entity
        response, error = await self.call_tool("hard_delete_entity", {
            "entity_id": "hard-delete-test",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_entity", "13.4_already_deleted", response, error,
                          is_acceptable=True)  # Should be idempotent
        
        # Test 13.5: Hard delete entity with relationships (cascade)
        await self.call_tool("add_entity", {
            "entity_id": "cascade-delete-source",
            "entity_type": "test",
            "name": "Source for Cascade Delete",
            "group_id": "regression-test"
        })
        await self.call_tool("add_entity", {
            "entity_id": "cascade-delete-target",
            "entity_type": "test",
            "name": "Target for Cascade Delete",
            "group_id": "regression-test"
        })
        await self.call_tool("add_relationship", {
            "source_entity_id": "cascade-delete-source",
            "target_entity_id": "cascade-delete-target",
            "relationship_type": "CASCADE_TEST",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("hard_delete_entity", {
            "entity_id": "cascade-delete-source",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_entity", "13.5_cascade_delete", response, error)
        # Verify relationships are also deleted
        rel_response, rel_error = await self.call_tool("get_entity_relationships", {
            "entity_id": "cascade-delete-source",
            "direction": "outgoing",
            "group_id": "regression-test"
        })
        if not rel_error and isinstance(rel_response, dict):
            relationships = rel_response.get("relationships", [])
            if len(relationships) == 0:
                self.record_result("hard_delete_entity", "13.5_cascade_verified", 
                                 {"relationships_deleted": True}, None)
            else:
                self.record_result("hard_delete_entity", "13.5_cascade_verified", 
                                 None, "Relationships not deleted", is_blocker=True)
        
        # Test 13.6: Wrong group_id
        await self.call_tool("add_entity", {
            "entity_id": "wrong-group-entity",
            "entity_type": "test",
            "name": "Wrong Group Entity",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("hard_delete_entity", {
            "entity_id": "wrong-group-entity",
            "group_id": "wrong-group"
        })
        self.record_result("hard_delete_entity", "13.6_wrong_group_id", response, error,
                          is_acceptable=True)
        # Clean up
        await self.call_tool("hard_delete_entity", {
            "entity_id": "wrong-group-entity",
            "group_id": "regression-test"
        })
    
    # ========== TOOL 14: hard_delete_relationship ==========
    async def test_hard_delete_relationship(self):
        """Test hard_delete_relationship tool."""
        print("\n[TEST] hard_delete_relationship")
        
        # Setup: Create relationship for deletion
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_TEST",
            "group_id": "regression-test"
        })
        
        # Test 14.1: Happy path
        response, error = await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_relationship", "14.1_happy_path", response, error)
        
        # Test 14.2: Missing source_entity_id
        response, error = await self.call_tool("hard_delete_relationship", {
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_relationship", "14.2_missing_source", response, error,
                          is_acceptable=True)
        
        # Test 14.3: Non-existent relationship
        response, error = await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "NON_EXISTENT_REL",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_relationship", "14.3_nonexistent_relationship", response, error,
                          is_acceptable=True)
        
        # Test 14.4: Already hard-deleted relationship
        response, error = await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "HARD_DELETE_TEST",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_relationship", "14.4_already_deleted", response, error,
                          is_acceptable=True)  # Should be idempotent
        
        # Test 14.5: Hard delete soft-deleted relationship
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_THEN_HARD_DELETE",
            "group_id": "regression-test"
        })
        await self.call_tool("soft_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_THEN_HARD_DELETE",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "SOFT_THEN_HARD_DELETE",
            "group_id": "regression-test"
        })
        self.record_result("hard_delete_relationship", "14.5_hard_delete_soft_deleted", response, error)
        
        # Test 14.6: Wrong group_id
        await self.call_tool("add_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "WRONG_GROUP_REL",
            "group_id": "regression-test"
        })
        response, error = await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "WRONG_GROUP_REL",
            "group_id": "wrong-group"
        })
        self.record_result("hard_delete_relationship", "14.6_wrong_group_id", response, error,
                          is_acceptable=True)
        # Clean up
        await self.call_tool("hard_delete_relationship", {
            "source_entity_id": "rel-source-001",
            "target_entity_id": "rel-target-001",
            "relationship_type": "WRONG_GROUP_REL",
            "group_id": "regression-test"
        })
    
    # ========== MAIN TEST RUNNER ==========
    async def run_all_tests(self):
        """Run all regression tests."""
        print("=" * 80)
        print("GRAFFITI GRAPH MCP - COMPREHENSIVE REGRESSION TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        try:
            await self.setup()
            
            # Run all test suites
            await self.test_add_entity()
            await self.test_add_relationship()
            await self.test_get_entity_by_id()
            await self.test_get_entities_by_type()
            await self.test_get_entity_relationships()
            await self.test_search_nodes()
            await self.test_add_memory()
            await self.test_update_memory()
            await self.test_soft_delete_entity()
            await self.test_soft_delete_relationship()
            await self.test_restore_entity()
            await self.test_restore_relationship()
            await self.test_hard_delete_entity()
            await self.test_hard_delete_relationship()
            
        finally:
            await self.teardown()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 80)
        print("TEST REPORT")
        print("=" * 80)
        print(f"Completed at: {datetime.now().isoformat()}")
        print()
        
        # Count results
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        acceptable = len([r for r in self.results if r.status == "ACCEPTABLE"])
        blockers = len([r for r in self.results if r.status == "BLOCKER"])
        
        print(f"Total Tests: {total}")
        print(f"  [OK] Passed: {passed}")
        print(f"  [WARN] Acceptable Failures: {acceptable}")
        print(f"  [FAIL] Blockers: {blockers}")
        print()
        
        # Group by tool
        tools = {}
        for result in self.results:
            if result.tool_name not in tools:
                tools[result.tool_name] = {"PASS": 0, "ACCEPTABLE": 0, "BLOCKER": 0}
            tools[result.tool_name][result.status] += 1
        
        print("Results by Tool:")
        print("-" * 80)
        for tool_name in sorted(tools.keys()):
            stats = tools[tool_name]
            total_tool = sum(stats.values())
            print(f"{tool_name:30s} Total: {total_tool:3d} | "
                  f"Pass: {stats['PASS']:3d} | "
                  f"Warn: {stats['ACCEPTABLE']:3d} | "
                  f"Fail: {stats['BLOCKER']:3d}")
        print()
        
        # List all blockers
        blocker_results = [r for r in self.results if r.status == "BLOCKER"]
        if blocker_results:
            print("=" * 80)
            print("BLOCKER ISSUES (Need Immediate Fix):")
            print("=" * 80)
            for result in blocker_results:
                print(f"\n[FAIL] {result.tool_name}::{result.test_name}")
                print(f"  Error: {result.error}")
                if result.response:
                    print(f"  Response: {json.dumps(result.response, indent=2)[:200]}...")
            print()
        
        # List acceptable failures
        acceptable_results = [r for r in self.results if r.status == "ACCEPTABLE"]
        if acceptable_results:
            print("=" * 80)
            print("ACCEPTABLE FAILURES (Expected Behavior):")
            print("=" * 80)
            for result in acceptable_results[:10]:  # Show first 10
                print(f"[WARN] {result.tool_name}::{result.test_name}")
                if result.error:
                    print(f"  Error: {result.error[:100]}...")
            if len(acceptable_results) > 10:
                print(f"\n... and {len(acceptable_results) - 10} more acceptable failures")
            print()
        
        # Summary
        print("=" * 80)
        if blockers == 0:
            print("[OK] NO BLOCKERS FOUND - All critical tests passed!")
        else:
            print(f"[FAIL] {blockers} BLOCKER(S) FOUND - Immediate fixes required!")
        print("=" * 80)


async def main():
    """Main entry point."""
    tester = RegressionTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)