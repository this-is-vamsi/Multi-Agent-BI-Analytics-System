$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$env:PYTHONPATH = ".;.deps"
$env:MPLCONFIGDIR = "data\matplotlib"

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if ($name -and $value) {
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}
$PythonExe = if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    "$ProjectRoot\.venv\Scripts\python.exe"
} else {
    (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Error "Python executable not found. Please create a virtual environment (.venv) or ensure Python is in PATH."
    exit 1
}

& $PythonExe -m streamlit run ui\streamlit_app.py --global.developmentMode false --server.address 127.0.0.1 --server.port 8501
