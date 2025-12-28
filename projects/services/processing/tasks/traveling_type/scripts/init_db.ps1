
# Get the directory of the script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.Parent.Parent.FullName

Write-Host "Project root detected as: $ProjectRoot"

# Set PYTHONPATH
$env:PYTHONPATH = "$ProjectRoot;$env:PYTHONPATH"

# Check if .env needs to be loaded manually (briefly check, python script already does it but helping env here is good)
if (Test-Path "$ScriptDir\.env") {
    Write-Host "Loading .env from $ScriptDir"
    Get-Content "$ScriptDir\.env" | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Run the initialization script
Write-Host "Running database initialization..."
python "$ScriptDir\init_db.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database initialized successfully." -ForegroundColor Green
} else {
    Write-Host "❌ Database initialization failed." -ForegroundColor Red
    exit 1
}
