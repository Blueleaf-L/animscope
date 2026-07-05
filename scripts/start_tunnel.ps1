# Public tunnel for PowerShell
# Usage: .\scripts\start_tunnel.ps1
# If execution policy blocks, run: powershell -ExecutionPolicy Bypass -File scripts\start_tunnel.ps1

$port = 8000
Write-Host "Starting tunnel on port $port..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

while ($true) {
  Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Connecting..."
  ssh -o StrictHostKeyChecking=no `
      -o ServerAliveInterval=30 `
      -o ServerAliveCountMax=3 `
      -o ExitOnForwardFailure=yes `
      -R 80:localhost:$port `
      localhost.run 2>&1 | ForEach-Object {
    $line = $_
    Write-Host $line
    if ($line -match '(https://[^\s]*\.lhr\.life)') {
      Write-Host ""
      Write-Host "==============================================" -ForegroundColor Cyan
      Write-Host "  PUBLIC URL: $($matches[1])" -ForegroundColor Cyan
      Write-Host "==============================================" -ForegroundColor Cyan
      Write-Host ""
    }
  }
  Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Disconnected. Reconnecting in 5s..." -ForegroundColor Yellow
  Start-Sleep -Seconds 5
}
