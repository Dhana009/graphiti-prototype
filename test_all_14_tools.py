"""
Test script to verify all 14 MCP tools are working.
This script tests the graphiti-graph MCP server (stdio).
"""

import asyncio
import json
import sys
from typing import Any, Dict

# The 14 tools to test
ALL_TOOLS = [
    "add_entity",
    "add_relationship", 
    "get_entity_by_id",
    "get_entities_by_type",
    "get_entity_relationships",
    "search_nodes",
    "add_memory",
    "update_memory",
    "soft_delete_entity",
    "soft_delete_relationship",
    "restore_entity",
    "restore_relationship",
    "hard_delete_entity",
    "hard_delete_relationship",
]

# Test data
TEST_ENTITY_ID = "test_entity_001"
TEST_ENTITY_TYPE = "Person"
TEST_ENTITY_NAME = "Test Person"
TEST_ENTITY_ID_2 = "test_entity_002"
TEST_RELATIONSHIP_TYPE = "KNOWS"
TEST_MEMORY_NAME = "test_memory_001"
TEST_MEMORY_BODY = "This is a test memory about testing the MCP tools."


async def test_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single MCP tool."""
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print(f"{'='*60}")
    
    try:
        # Import the MCP tool handler
        from graffiti_mcp_implementation.src.mcp_server import handle_call_tool
        from graffiti_mcp_implementation.src.database import DatabaseConnection, initialize_database
        
        # Initialize database connection
        connection = await initialize_database()
        
        # Call the tool
        result = await handle_call_tool(tool_name, arguments)
        
        # Extract text content
        if result and len(result) > 0:
            result_text = result[0].text
            result_data = json.loads(result_text)
            print(f"✅ SUCCESS: {tool_name}")
            print(f"Result: {json.dumps(result_data, indent=2)}")
            return {"tool": tool_name, "status": "success", "result": result_data}
        else:
            print(f"⚠️  WARNING: {tool_name} returned empty result")
            return {"tool": tool_name, "status": "warning", "result": None}
            
    except Exception as e:
        print(f"❌ FAILED: {tool_name}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"tool": tool_name, "status": "failed", "error": str(e)}


async def test_all_tools():
    """Test all 14 MCP tools in sequence."""
    print("\n" + "="*60)
    print("TESTING ALL 14 MCP TOOLS")
    print("="*60)
    
    results = []
    
    # 1. add_entity
    results.append(await test_tool("add_entity", {
        "entity_id": TEST_ENTITY_ID,
        "entity_type": TEST_ENTITY_TYPE,
        "name": TEST_ENTITY_NAME,
        "group_id": "main"
    }))
    
    # 2. add_entity (second entity for relationships)
    results.append(await test_tool("add_entity", {
        "entity_id": TEST_ENTITY_ID_2,
        "entity_type": TEST_ENTITY_TYPE,
        "name": "Test Person 2",
        "group_id": "main"
    }))
    
    # 3. get_entity_by_id
    results.append(await test_tool("get_entity_by_id", {
        "entity_id": TEST_ENTITY_ID,
        "group_id": "main"
    }))
    
    # 4. get_entities_by_type
    results.append(await test_tool("get_entities_by_type", {
        "entity_type": TEST_ENTITY_TYPE,
        "group_id": "main",
        "limit": 10
    }))
    
    # 5. add_relationship
    results.append(await test_tool("add_relationship", {
        "source_entity_id": TEST_ENTITY_ID,
        "target_entity_id": TEST_ENTITY_ID_2,
        "relationship_type": TEST_RELATIONSHIP_TYPE,
        "group_id": "main"
    }))
    
    # 6. get_entity_relationships
    results.append(await test_tool("get_entity_relationships", {
        "entity_id": TEST_ENTITY_ID,
        "group_id": "main",
        "direction": "outgoing"
    }))
    
    # 7. search_nodes
    results.append(await test_tool("search_nodes", {
        "query": "Test Person",
        "group_id": "main",
        "max_nodes": 5
    }))
    
    # 8. add_memory
    memory_result = await test_tool("add_memory", {
        "name": TEST_MEMORY_NAME,
        "episode_body": TEST_MEMORY_BODY,
        "group_id": "main"
    })
    results.append(memory_result)
    
    # Extract memory UUID if available
    memory_uuid = None
    if memory_result.get("status") == "success" and "result" in memory_result:
        try:
            result_data = memory_result["result"]
            if isinstance(result_data, dict) and "uuid" in result_data:
                memory_uuid = result_data["uuid"]
        except:
            pass
    
    # 9. update_memory (if we have a UUID)
    if memory_uuid:
        results.append(await test_tool("update_memory", {
            "uuid": memory_uuid,
            "episode_body": "Updated test memory content",
            "group_id": "main"
        }))
    else:
        print("\n⚠️  Skipping update_memory - no UUID from add_memory")
        results.append({"tool": "update_memory", "status": "skipped", "reason": "no_uuid"})
    
    # 10. soft_delete_entity
    results.append(await test_tool("soft_delete_entity", {
        "entity_id": TEST_ENTITY_ID_2,
        "group_id": "main"
    }))
    
    # 11. soft_delete_relationship
    results.append(await test_tool("soft_delete_relationship", {
        "source_entity_id": TEST_ENTITY_ID,
        "target_entity_id": TEST_ENTITY_ID_2,
        "relationship_type": TEST_RELATIONSHIP_TYPE,
        "group_id": "main"
    }))
    
    # 12. restore_entity
    results.append(await test_tool("restore_entity", {
        "entity_id": TEST_ENTITY_ID_2,
        "group_id": "main"
    }))
    
    # 13. restore_relationship
    results.append(await test_tool("restore_relationship", {
        "source_entity_id": TEST_ENTITY_ID,
        "target_entity_id": TEST_ENTITY_ID_2,
        "relationship_type": TEST_RELATIONSHIP_TYPE,
        "group_id": "main"
    }))
    
    # 14. hard_delete_relationship
    results.append(await test_tool("hard_delete_relationship", {
        "source_entity_id": TEST_ENTITY_ID,
        "target_entity_id": TEST_ENTITY_ID_2,
        "relationship_type": TEST_RELATIONSHIP_TYPE,
        "group_id": "main"
    }))
    
    # 15. hard_delete_entity (cleanup)
    results.append(await test_tool("hard_delete_entity", {
        "entity_id": TEST_ENTITY_ID_2,
        "group_id": "main"
    }))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    failed_count = sum(1 for r in results if r.get("status") == "failed")
    skipped_count = sum(1 for r in results if r.get("status") == "skipped")
    
    print(f"\nTotal tools tested: {len(results)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result.get("status") == "success" else "❌" if result.get("status") == "failed" else "⚠️"
        print(f"{i:2d}. {status_icon} {result.get('tool', 'unknown')}: {result.get('status', 'unknown')}")
        if result.get("status") == "failed":
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    # Check if all 14 core tools were tested
    unique_tools = set(r.get("tool") for r in results)
    core_tools_tested = [t for t in ALL_TOOLS if t in unique_tools]
    
    print(f"\n{'='*60}")
    print(f"CORE 14 TOOLS STATUS: {len(core_tools_tested)}/14 tested")
    print("="*60)
    
    for tool in ALL_TOOLS:
        if tool in unique_tools:
            tool_results = [r for r in results if r.get("tool") == tool]
            tool_status = tool_results[0].get("status") if tool_results else "not_tested"
            status_icon = "✅" if tool_status == "success" else "❌" if tool_status == "failed" else "⚠️"
            print(f"{status_icon} {tool}: {tool_status}")
        else:
            print(f"❌ {tool}: NOT TESTED")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(test_all_tools())
        
        # Exit with error code if any failed
        failed = any(r.get("status") == "failed" for r in results)
        sys.exit(1 if failed else 0)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

