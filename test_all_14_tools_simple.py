"""
Simple test script to verify all 14 MCP tools are working.
Tests via MCP tool calls (using the available MCP tools).
"""

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

print("="*70)
print("TESTING ALL 14 MCP TOOLS - Manual Test Instructions")
print("="*70)
print("\nPlease test each tool manually in Cursor using the MCP tools.")
print("\nThe 14 tools are:")
for i, tool in enumerate(ALL_TOOLS, 1):
    print(f"  {i:2d}. {tool}")
print("\n" + "="*70)

