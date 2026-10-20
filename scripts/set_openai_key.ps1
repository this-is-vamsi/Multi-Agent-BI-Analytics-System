$ErrorActionPreference = "Stop"

$key = Read-Host "Paste OPENAI_API_KEY"
if (-not $key -or -not $key.StartsWith("sk-")) {
    Write-Host "That does not look like an OpenAI API key. No changes made."
    exit 1
}

$envPath = Join-Path (Split-Path -Parent $PSScriptRoot) ".env"
if (Test-Path $envPath) {
    $lines = Get-Content $envPath
} else {
    $lines = @()
}

$updated = $false
$newLines = foreach ($line in $lines) {
    if ($line -match "^OPENAI_API_KEY=") {
        $updated = $true
        "OPENAI_API_KEY=$key"
    } else {
        $line
    }
}

if (-not $updated) {
    $newLines += "OPENAI_API_KEY=$key"
}

Set-Content -Path $envPath -Value $newLines -Encoding UTF8
Write-Host "OPENAI_API_KEY updated in .env. Restart the API service windows to use Live LLM mode."
