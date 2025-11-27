# Troubleshooting Guide

## 🔴 Authentication Failure

**Error:** `Neo4j authentication failed: The client is unauthorized`

**Cause:** Neo4j Docker container was initialized with a different password than what the MCP server is using. Neo4j only sets the password on FIRST initialization - if the database volume already exists, it keeps the old password.

**Solution:** Reset Neo4j completely to reinitialize with the correct password.

### Quick Fix

```powershell
# Stop and remove everything (including volumes)
docker-compose down -v

# Start fresh with correct password
docker-compose up -d

# Wait 30-60 seconds for Neo4j to become healthy
docker-compose ps
```

### Verify Password Reset

After resetting, Neo4j will be initialized with:
- **Username:** `neo4j`
- **Password:** `testpassword`

You can verify in Neo4j Browser: http://localhost:7474

---

## ✅ Connection Refused

**Error:** `Connection refused` or `Couldn't connect to localhost:7687`

**Cause:** Neo4j container is not running.

**Solution:**
```powershell
docker-compose up -d
docker-compose ps  # Wait for "healthy" status
```

---

## 📋 Current Status Check

**Check if Neo4j is running:**
```powershell
docker-compose ps
```

**View authentication errors:**
```powershell
docker-compose logs neo4j | Select-String "authentication"
```

**View all recent logs:**
```powershell
docker-compose logs --tail 50 neo4j
```

---

## 🔄 Complete Reset Workflow

If you need a completely fresh start:

```powershell
# 1. Stop everything
docker-compose down -v

# 2. Remove any orphaned containers
docker container prune -f

# 3. Start fresh
docker-compose up -d

# 4. Wait for healthy status (check every 5 seconds)
docker-compose ps

# 5. Verify you can access Neo4j Browser
# Open: http://localhost:7474
# Login: neo4j / testpassword
```

---

## 💡 Why This Happens

Neo4j stores the database password in the data volume. When you use `docker-compose down`, it stops the container but keeps the volumes (so your data persists). When you restart, Neo4j uses the existing password from the volume.

The `NEO4J_AUTH` environment variable in `docker-compose.yml` only works when creating a NEW database. If the volume already exists, Neo4j ignores this setting.

**To change the password in an existing database:**
1. Access Neo4j Browser: http://localhost:7474
2. Login with the OLD password
3. Change password in settings, OR
4. Reset completely: `docker-compose down -v` (deletes all data)

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose ps` | Check container status |
| `docker-compose logs neo4j` | View Neo4j logs |
| `docker-compose up -d` | Start Neo4j |
| `docker-compose down` | Stop Neo4j (keeps data) |
| `docker-compose down -v` | Stop and delete everything |
| `docker-compose restart` | Restart container |


