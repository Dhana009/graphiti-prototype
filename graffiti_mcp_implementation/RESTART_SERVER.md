# Restarting Graffiti Graph MCP Server

## Steps to Restart

1. **Restart your MCP client (Cursor/Claude Desktop)**:
   - Close and reopen Cursor (or your MCP client)
   - The MCP server will automatically restart with the new configuration

2. **Verify Neo4j is running**:
   ```bash
   docker-compose ps
   ```
   Should show `graffiti-neo4j-test` as running

3. **Test the server**:
   After restarting Cursor, the MCP tools should be available with the new `gpt-5-nano` configuration.

## Configuration Changes

- Default LLM model changed to `gpt-5-nano`
- Temperature handling updated for reasoning models
- MCP config includes `OPENAI_LLM_MODEL=gpt-5-nano`

## After Restart

Test the MCP tools to verify:
- `add_memory` works with `gpt-5-nano`
- Entity/relationship extraction functions correctly
- No temperature parameter errors


