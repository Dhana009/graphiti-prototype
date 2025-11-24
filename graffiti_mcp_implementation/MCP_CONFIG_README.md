# MCP Server Configuration

This directory contains the MCP server configuration file for integrating the Graffiti Graph MCP server with Cursor, Claude Desktop, or other MCP-compatible clients.

## Configuration File

### `mcp-config.json`

This file contains the MCP server configuration. You need to copy this configuration to your MCP client's settings file.

**For Cursor IDE:**
- Location: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` (Windows)
- Or: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` (Linux/Mac)

**For Claude Desktop:**
- Location: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- Or: `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)
- Or: `~/.config/Claude/claude_desktop_config.json` (Linux)

## Setup Instructions

1. **Update the path in `mcp-config.json`:**
   - Replace `D:\\planning\\FlowHUB-draft2\\graphiti\\graffiti_mcp_implementation\\main.py` with your absolute path
   - Use forward slashes `/` or escaped backslashes `\\` depending on your OS

2. **Set environment variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key (required for embeddings and entity extraction)
   - The Neo4j connection details are set in the `env` section, but you can also use a `.env` file

3. **Copy configuration to your MCP client:**
   - Open your MCP client's settings file
   - Merge the `mcpServers` section from `mcp-config.json` into the existing configuration
   - Save the file and restart your MCP client

## Configuration Details

- **Server Name:** `graffiti-graph`
- **Command:** `uv` (uses uv package manager to run Python)
- **Transport:** `stdio` (standard input/output)
- **Environment Variables:**
  - `NEO4J_URI`: Neo4j connection URI (default: `bolt://localhost:7687`)
  - `NEO4J_USER`: Neo4j username (default: `neo4j`)
  - `NEO4J_PASSWORD`: Neo4j password (default: `testpassword`)
  - `OPENAI_API_KEY`: OpenAI API key (required, uses `${OPENAI_API_KEY}` to read from system environment)

## Testing the Configuration

After adding the configuration to your MCP client:

1. **Restart your MCP client** (Cursor/Claude Desktop)

2. **Verify the server is running:**
   - Check the MCP client logs for connection messages
   - The server should initialize and connect to Neo4j

3. **Test the tools:**
   - Try calling one of the 14 available tools:
     - `add_entity`
     - `add_relationship`
     - `get_entity_by_id`
     - `search_nodes`
     - `add_memory`
     - etc.

## Troubleshooting

### Server Not Starting

1. **Check the path:**
   - Ensure the path to `main.py` is correct and absolute
   - Verify the file exists at that location

2. **Check uv is installed:**
   - Run `uv --version` to verify uv is in your PATH
   - If not, install it: `pip install uv` or `cargo install uv`

3. **Check environment variables:**
   - Verify `OPENAI_API_KEY` is set in your system environment
   - Check Neo4j is running: `docker-compose ps` (if using Docker)

### Connection Errors

1. **Neo4j not running:**
   - Start Neo4j: `docker-compose up -d`
   - Verify connection: Check Neo4j Browser at `http://localhost:7474`

2. **Wrong credentials:**
   - Verify `NEO4J_PASSWORD` matches your Neo4j password
   - Default password in docker-compose.yml is `testpassword`

### Tool Not Found

1. **Server not initialized:**
   - Check server logs for initialization errors
   - Verify database connection is successful

2. **Tool name mismatch:**
   - All 14 tools should be available
   - Check `handle_list_tools()` returns all tools

## Example Configuration

```json
{
  "mcpServers": {
    "graffiti-graph": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "D:\\planning\\FlowHUB-draft2\\graphiti\\graffiti_mcp_implementation\\main.py"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "testpassword",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

## Alternative: Using Python Directly

If you prefer not to use `uv`, you can modify the configuration to use Python directly:

```json
{
  "mcpServers": {
    "graffiti-graph": {
      "command": "python",
      "args": [
        "D:\\planning\\FlowHUB-draft2\\graphiti\\graffiti_mcp_implementation\\main.py"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "testpassword",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

**Note:** When using Python directly, ensure:
- Virtual environment is activated, OR
- All dependencies are installed globally, OR
- Use the full path to the Python interpreter in your virtual environment


