$procs = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $procs) {
    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    Write-Host "Killed PID $p"
}
if (-not $procs) {
    Write-Host "No process on port 5000"
}
