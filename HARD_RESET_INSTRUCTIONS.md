# Hard Reset Instructions

## 1. Hard Reset Docker Containers

### Option A: Complete Reset (Removes All Data)
```powershell
# Navigate to docker directory
cd d:\graphiti_prototype\mcp_server\docker

# Stop and remove containers, networks, and volumes
docker-compose -f docker-compose-neo4j.yml down -v

# Remove any orphaned containers
docker-compose -f docker-compose-neo4j.yml down --remove-orphans

# Remove the Docker images (optional - forces rebuild)
docker rmi zepai/knowledge-graph-mcp:standalone 2>$null
docker rmi neo4j:5.26.0 2>$null

# Rebuild and start fresh
docker-compose -f docker-compose-neo4j.yml up -d --build
```

### Option B: Soft Reset (Keeps Data, Rebuilds Code)
```powershell
# Navigate to docker directory
cd d:\graphiti_prototype\mcp_server\docker

# Stop containers
docker-compose -f docker-compose-neo4j.yml down

# Rebuild with no cache (ensures latest code)
docker-compose -f docker-compose-neo4j.yml build --no-cache

# Start containers
docker-compose -f docker-compose-neo4j.yml up -d
```

### Option C: Quick Restart (Fastest)
```powershell
cd d:\graphiti_prototype\mcp_server\docker
docker-compose -f docker-compose-neo4j.yml restart
```

## 2. Hard Reset MCP Server in Cursor

### Step 1: Stop All MCP Server Processes
```powershell
# Find and kill Python processes running the MCP server
Get-Process | Where-Object {$_.Path -like "*graffiti_mcp_implementation*" -or $_.CommandLine -like "*main.py*"} | Stop-Process -Force

# Or kill all Python processes (be careful!)
# Get-Process python | Stop-Process -Force
# Get-Process pythonw | Stop-Process -Force
```

### Step 2: Clear Cursor Cache
```powershell
# Close Cursor completely first, then:
# Navigate to Cursor cache directory
$cursorCache = "$env:APPDATA\Cursor\Cache"
if (Test-Path $cursorCache) {
    Remove-Item -Path "$cursorCache\*" -Recurse -Force
    Write-Host "Cursor cache cleared"
}
```

### Step 3: Restart Cursor
1. Close Cursor completely (check Task Manager for any remaining processes)
2. Wait 5 seconds
3. Reopen Cursor
4. The MCP server should reload automatically

### Step 4: Verify MCP Server Connection
1. Open Cursor Settings → MCP
2. Check that `graphiti-graph` is enabled
3. Look for any error messages
4. Check the MCP output panel for connection status

## 3. Complete System Reset (Nuclear Option)

### Full Reset Script
```powershell
# Save this as reset-all.ps1

Write-Host "=== Hard Reset Script ===" -ForegroundColor Yellow

# 1. Stop Docker containers
Write-Host "`n1. Stopping Docker containers..." -ForegroundColor Cyan
cd d:\graphiti_prototype\mcp_server\docker
docker-compose -f docker-compose-neo4j.yml down -v
docker-compose -f docker-compose-neo4j.yml down --remove-orphans

# 2. Kill Python processes
Write-Host "`n2. Killing Python processes..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*graphiti*" -or $_.Path -like "*graffiti*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*graphiti*" -or $_.Path -like "*graffiti*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Clear Cursor cache
Write-Host "`n3. Clearing Cursor cache..." -ForegroundColor Cyan
$cursorCache = "$env:APPDATA\Cursor\Cache"
if (Test-Path $cursorCache) {
    Remove-Item -Path "$cursorCache\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   Cache cleared" -ForegroundColor Green
}

# 4. Rebuild Docker
Write-Host "`n4. Rebuilding Docker containers..." -ForegroundColor Cyan
docker-compose -f docker-compose-neo4j.yml build --no-cache
docker-compose -f docker-compose-neo4j.yml up -d

Write-Host "`n=== Reset Complete ===" -ForegroundColor Green
Write-Host "Please restart Cursor manually" -ForegroundColor Yellow
```

## 4. Verify After Reset

### Check Docker Status
```powershell
cd d:\graphiti_prototype\mcp_server\docker
docker-compose -f docker-compose-neo4j.yml ps
docker-compose -f docker-compose-neo4j.yml logs --tail=20 graphiti-mcp
```

### Check MCP Server in Cursor
1. Open Cursor
2. Check MCP Settings → `graphiti-graph` should be enabled
3. Test with a simple tool call
4. Check logs in Cursor's MCP output panel

## 5. Troubleshooting

### If MCP server still uses old code:
1. Verify the code path in `mcp.json`:
   - Should point to: `D:\planning\graphiti_prototype\graffiti_mcp_implementation\main.py`
2. Check if there are multiple Python environments:
   - The server might be using a different Python installation
3. Verify file changes were saved:
   - Check `graffiti_mcp_implementation/src/validation.py` has `'main'` as default
4. Check for cached Python bytecode:
   ```powershell
   # Remove .pyc files
   Get-ChildItem -Path "d:\planning\graphiti_prototype\graffiti_mcp_implementation" -Recurse -Filter "*.pyc" | Remove-Item -Force
   Get-ChildItem -Path "d:\planning\graphiti_prototype\graffiti_mcp_implementation" -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
   ```


