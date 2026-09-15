$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    py -3 -m app.main --port 8765 --data-dir (Join-Path $Root 'sesiones')
}
finally {
    Pop-Location
}
