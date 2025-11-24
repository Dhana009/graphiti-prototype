# Docker Compose Setup for Neo4j Testing

This document explains how to use Docker Compose to run Neo4j for integration testing.

## Quick Start

### Option 1: Using Docker Compose (Command Line)

```bash
docker-compose up -d
```

This will:
- Start Neo4j container in detached mode
- Expose ports 7474 (HTTP) and 7687 (Bolt)
- Create persistent volumes for data and logs
- Wait for Neo4j to be healthy before marking as ready

### Option 2: Using Docker MCP (AI Assistant)

The AI assistant can control Docker directly using the Docker MCP tools. This allows for:
- Programmatic container management
- Automated testing workflows
- Direct Docker CLI access through MCP

**Available Docker MCP Commands:**
- Start Neo4j: `docker-compose up -d`
- Check status: `docker-compose ps`
- View logs: `docker-compose logs neo4j`
- Stop Neo4j: `docker-compose stop`
- Remove containers: `docker-compose down`

### 2. Verify Neo4j is Running

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs neo4j

# Access Neo4j Browser (optional)
# Open http://localhost:7474 in your browser
# Login with: neo4j / testpassword
```

### 3. Stop Neo4j

```bash
# Stop containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove containers + volumes (deletes all data)
docker-compose down -v
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`) to customize configuration:

```bash
cp .env.example .env
```

Key variables:
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `testpassword`)
- `NEO4J_URI`: Connection URI (default: `bolt://localhost:7687`)

### Connection Settings

For integration tests, use these connection settings:

```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "testpassword"  # or from .env file
```

## Testing Workflow

### Before Running Tests

1. **Start Neo4j:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for health check:**
   ```bash
   docker-compose ps  # Should show "healthy" status
   ```

3. **Run tests:**
   ```bash
   pytest tests/integration/
   ```

### After Running Tests

1. **Stop Neo4j (optional):**
   ```bash
   docker-compose stop
   ```

2. **Clean up test data (if needed):**
   ```bash
   # Option 1: Reset database (keeps container)
   docker-compose exec neo4j cypher-shell -u neo4j -p testpassword "MATCH (n) DETACH DELETE n"
   
   # Option 2: Remove volumes and restart (fresh start)
   docker-compose down -v
   docker-compose up -d
   ```

## Troubleshooting

### Neo4j Won't Start

1. **Check if ports are already in use:**
   ```bash
   # Windows
   netstat -ano | findstr :7687
   netstat -ano | findstr :7474
   
   # Linux/Mac
   lsof -i :7687
   lsof -i :7474
   ```

2. **Check Docker logs:**
   ```bash
   docker-compose logs neo4j
   ```

3. **Check container status:**
   ```bash
   docker-compose ps
   ```

### Connection Refused

1. **Verify Neo4j is healthy:**
   ```bash
   docker-compose ps  # Should show "healthy"
   ```

2. **Test connection manually:**
   ```bash
   # Using cypher-shell (if installed)
   cypher-shell -a bolt://localhost:7687 -u neo4j -p testpassword
   ```

3. **Check firewall settings** (if applicable)

### Reset Everything

If you need a completely fresh start:

```bash
# Stop and remove everything
docker-compose down -v

# Remove any orphaned containers
docker container prune -f

# Start fresh
docker-compose up -d
```

## CI/CD Integration

For CI/CD pipelines, you can use the same docker-compose file:

```yaml
# Example GitHub Actions
- name: Start Neo4j
  run: docker-compose up -d
  
- name: Wait for Neo4j
  run: |
    timeout 60 bash -c 'until docker-compose ps | grep -q healthy; do sleep 2; done'
  
- name: Run tests
  run: pytest tests/integration/
  
- name: Stop Neo4j
  run: docker-compose down -v
```

## Docker MCP Integration

The project uses Docker MCP for programmatic Docker management. The AI assistant can:

1. **Start/Stop Containers:** Automatically manage Neo4j lifecycle during testing
2. **Check Health:** Verify container status before running tests
3. **View Logs:** Access container logs for debugging
4. **Clean Up:** Remove containers and volumes when needed

**Example MCP Workflow:**
- Before tests: AI assistant starts Neo4j using Docker MCP
- During tests: AI assistant monitors container health
- After tests: AI assistant can stop or reset containers as needed

This integration enables fully automated testing workflows without manual Docker management.

## Notes

- **Data Persistence:** Data is stored in Docker volumes (`neo4j_data`, `neo4j_logs`)
- **Port Conflicts:** If ports 7474 or 7687 are already in use, modify the port mappings in `docker-compose.yml`
- **Memory Settings:** Default memory settings are suitable for testing. Adjust if needed for larger datasets.
- **Health Check:** The health check ensures Neo4j is ready before tests run. Wait for "healthy" status.
- **Docker MCP:** The AI assistant can manage Docker containers directly using MCP tools for automated workflows

## Next Steps

After Neo4j is running, proceed with:
1. Setting up environment variables (`.env` file)
2. Writing database connection tests (P1-1.1)
3. Implementing database connection code (P1-1.2)


