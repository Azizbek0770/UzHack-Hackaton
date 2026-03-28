$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"
Remove-Item -Recurse -Force ".\node_modules\.vite" -ErrorAction SilentlyContinue
npm run dev -- --host localhost --port 5173 --strictPort
