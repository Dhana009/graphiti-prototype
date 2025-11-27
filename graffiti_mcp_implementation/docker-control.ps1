# Docker Control Script for Neo4j
# Simple PowerShell script to manage Neo4j Docker container

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "reset", "help")]
    [string]$Action = "help"
)

function Show-Help {
    Write-Host @"
Docker Control Script for Neo4j

Usage: .\docker-control.ps1 [action]

Actions:
  start   - Start Neo4j container
  stop    - Stop Neo4j container (keeps data)
  restart - Restart Neo4j container
  status  - Show container status
  logs    - Show Neo4j logs (last 50 lines)
  reset   - Stop and remove everything (deletes data)
  help    - Show this help message

Examples:
  .\docker-control.ps1 start
  .\docker-control.ps1 logs
  .\docker-control.ps1 status
"@
}

switch ($Action) {
    "start" {
        Write-Host "Starting Neo4j container..." -ForegroundColor Green
        docker-compose up -d
        Write-Host "`nWaiting for Neo4j to become healthy..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        docker-compose ps
        Write-Host "`nNeo4j should be available at:" -ForegroundColor Cyan
        Write-Host "  Browser: http://localhost:7474" -ForegroundColor Cyan
        Write-Host "  Bolt:    bolt://localhost:7687" -ForegroundColor Cyan
    }
    
    "stop" {
        Write-Host "Stopping Neo4j container..." -ForegroundColor Yellow
        docker-compose stop
        Write-Host "Neo4j stopped (data preserved)" -ForegroundColor Green
    }
    
    "restart" {
        Write-Host "Restarting Neo4j container..." -ForegroundColor Yellow
        docker-compose restart
        Write-Host "`nWaiting for Neo4j to become healthy..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        docker-compose ps
    }
    
    "status" {
        Write-Host "Neo4j Container Status:" -ForegroundColor Cyan
        docker-compose ps
    }
    
    "logs" {
        Write-Host "Showing last 50 lines of Neo4j logs..." -ForegroundColor Cyan
        docker-compose logs --tail 50 neo4j
        Write-Host "`nTip: Use 'docker-compose logs -f neo4j' to follow logs in real-time" -ForegroundColor Yellow
    }
    
    "reset" {
        Write-Host "WARNING: This will delete all Neo4j data!" -ForegroundColor Red
        $confirm = Read-Host "Type 'yes' to confirm"
        if ($confirm -eq "yes") {
            Write-Host "Stopping and removing Neo4j container and volumes..." -ForegroundColor Yellow
            docker-compose down -v
            Write-Host "Reset complete. Use 'start' to create a fresh container." -ForegroundColor Green
        } else {
            Write-Host "Reset cancelled." -ForegroundColor Yellow
        }
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Show-Help
    }
}



