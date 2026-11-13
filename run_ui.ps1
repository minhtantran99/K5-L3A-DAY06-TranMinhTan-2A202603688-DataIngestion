$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & "$PSScriptRoot\.venv\Scripts\python.exe" -m starter.src.webapp --open
} finally {
    Pop-Location
}
