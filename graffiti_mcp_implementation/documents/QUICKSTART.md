# Quick Start Guide - Docker & Server Commands

Simple reference for managing Neo4j Docker container and MCP server.

## 🐳 Docker Commands (Neo4j Database)

### Start Neo4j
```bash
docker-compose up -d
```

### Stop Neo4j (keeps data)
```bash
docker-compose stop
```

### Stop and Remove Neo4j (keeps data)
```bash
docker-compose down
```

### Stop and Remove Everything (deletes data)
```bash
docker-compose down -v
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
# View all logs
docker-compose logs neo4j

# View last 50 lines
docker-compose logs --tail 50 neo4j

# Follow logs in real-time
docker-compose logs -f neo4j
```

### Restart Neo4j
```bash
docker-compose restart neo4j
```

### Access Neo4j Browser
Open in browser: http://localhost:7474
- Username: `neo4j`
- Password: `testpassword`

---

## 🚀 MCP Server Commands

### Install Dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Start Server Manually
```bash
# Method 1: Using Python directly
python main.py

# Method 2: Using uv
uv run main.py

# Method 3: Using module syntax
python -m src

# Method 4: Using entry point (if installed)
graffiti-mcp-server
```

### Build/Install Server
```bash
# Install in development mode
uv pip install -e .

# Or with dev dependencies
uv sync --extra dev
```

### Check if Server Can Connect
```bash
python test_server_connection.py
```

---

## 📊 Useful Status Checks

### Check if Neo4j is Running
```bash
docker-compose ps
# Look for "healthy" status
```

### Check if Ports are Available
```bash
# Windows PowerShell
netstat -ano | findstr :7687
netstat -ano | findstr :7474

# Check if something is using the ports
```

### View Docker Container Stats
```bash
docker stats graffiti-neo4j-test
```

---

## 🔄 Common Workflows

### Start Everything Fresh
```bash
# 1. Start Neo4j
docker-compose up -d

# 2. Wait for it to be healthy (30-60 seconds)
docker-compose ps

# 3. Start MCP server (in another terminal)
python main.py
```

### Restart Everything
```bash
# 1. Stop Neo4j
docker-compose restart

# 2. Wait for health check
docker-compose ps

# 3. Restart MCP server (Ctrl+C and restart)
```

### Complete Reset (Fresh Start)
```bash
# 1. Stop and remove everything
docker-compose down -v

# 2. Start fresh
docker-compose up -d

# 3. Wait for healthy status
docker-compose ps
```

### Debug Connection Issues
```bash
# 1. Check Neo4j is running
docker-compose ps

# 2. Check Neo4j logs
docker-compose logs neo4j

# 3. Test connection
python test_server_connection.py
```

---

## 📝 Default Configuration

- **Neo4j URI**: `bolt://localhost:7687`
- **Neo4j Username**: `neo4j`
- **Neo4j Password**: `testpassword`
- **Neo4j Browser**: http://localhost:7474
- **Container Name**: `graffiti-neo4j-test`

---

## 🆘 Troubleshooting

### "Connection refused" Error
1. Check Neo4j is running: `docker-compose ps`
2. Wait for "healthy" status
3. Check logs: `docker-compose logs neo4j`

### Port Already in Use
1. Check what's using the port: `netstat -ano | findstr :7687`
2. Stop conflicting service or change port in `docker-compose.yml`

### Server Won't Start
1. Check Neo4j is healthy first
2. Verify environment variables
3. Check server logs in terminal output

---

## 💡 Tips

- Always wait for Neo4j to show "healthy" status before starting MCP server
- Use `docker-compose logs -f` to monitor startup in real-time
- Data persists in Docker volumes even after stopping container
- Use `docker-compose down -v` to completely reset database

