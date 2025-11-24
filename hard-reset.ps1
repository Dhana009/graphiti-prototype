# Hard Reset Script for Graphiti MCP Server
# This script performs a complete reset of Docker containers and prepares for MCP server restart

Write-Host "=== Hard Reset Script ===" -ForegroundColor Yellow
Write-Host "This will:" -ForegroundColor Cyan
Write-Host "  1. Stop and remove Docker containers" -ForegroundColor White
Write-Host "  2. Kill Python processes related to MCP server" -ForegroundColor White
Write-Host "  3. Clear Cursor cache" -ForegroundColor White
Write-Host "  4. Rebuild Docker containers" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Continue? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Cancelled." -ForegroundColor Red
    exit
}

# 1. Stop Docker containers
Write-Host "`n[1/4] Stopping Docker containers..." -ForegroundColor Cyan
$dockerPath = "d:\graphiti_prototype\mcp_server\docker"
if (Test-Path $dockerPath) {
    Push-Location $dockerPath
    docker-compose -f docker-compose-neo4j.yml down -v 2>&1 | Out-Null
    docker-compose -f docker-compose-neo4j.yml down --remove-orphans 2>&1 | Out-Null
    Write-Host "   Docker containers stopped" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "   Docker path not found, skipping..." -ForegroundColor Yellow
}

# 2. Kill Python processes
Write-Host "`n[2/4] Killing Python processes..." -ForegroundColor Cyan
$killed = 0
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*graphiti*" -or 
    $_.Path -like "*graffiti*" -or
    $_.CommandLine -like "*main.py*"
} | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    $killed++
}
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*graphiti*" -or 
    $_.Path -like "*graffiti*"
} | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    $killed++
}
if ($killed -gt 0) {
    Write-Host "   Killed $killed Python process(es)" -ForegroundColor Green
} else {
    Write-Host "   No Python processes found to kill" -ForegroundColor Yellow
}

# 3. Clear Cursor cache
Write-Host "`n[3/4] Clearing Cursor cache..." -ForegroundColor Cyan
$cursorCache = "$env:APPDATA\Cursor\Cache"
if (Test-Path $cursorCache) {
    try {
        Get-ChildItem -Path $cursorCache -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "   Cursor cache cleared" -ForegroundColor Green
    } catch {
        Write-Host "   Could not clear cache (may be in use): $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Cache directory not found" -ForegroundColor Yellow
}

# 4. Remove Python bytecode cache
Write-Host "`n[3.5/4] Removing Python bytecode cache..." -ForegroundColor Cyan
$mcpPath = "d:\planning\graphiti_prototype\graffiti_mcp_implementation"
if (Test-Path $mcpPath) {
    Get-ChildItem -Path $mcpPath -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $mcpPath -Recurse -Filter "__pycache__" -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   Python bytecode cache cleared" -ForegroundColor Green
}

# 5. Rebuild Docker
Write-Host "`n[4/4] Rebuilding Docker containers..." -ForegroundColor Cyan
if (Test-Path $dockerPath) {
    Push-Location $dockerPath
    Write-Host "   Building (this may take a few minutes)..." -ForegroundColor Yellow
    docker-compose -f docker-compose-neo4j.yml build --no-cache 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Build successful" -ForegroundColor Green
        Write-Host "   Starting containers..." -ForegroundColor Yellow
        docker-compose -f docker-compose-neo4j.yml up -d 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   Containers started" -ForegroundColor Green
        } else {
            Write-Host "   Failed to start containers" -ForegroundColor Red
        }
    } else {
        Write-Host "   Build failed" -ForegroundColor Red
    }
    Pop-Location
} else {
    Write-Host "   Docker path not found, skipping..." -ForegroundColor Yellow
}

Write-Host "`n=== Reset Complete ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Close Cursor completely (check Task Manager)" -ForegroundColor White
Write-Host "  2. Wait 5 seconds" -ForegroundColor White
Write-Host "  3. Reopen Cursor" -ForegroundColor White
Write-Host "  4. Check MCP Settings → graphiti-graph should be enabled" -ForegroundColor White
Write-Host "  5. Test the MCP tools" -ForegroundColor White
Write-Host ""



