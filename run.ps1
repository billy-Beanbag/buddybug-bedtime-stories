Param(
	[switch]$Install
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
	py -3 -m venv .venv
}

. ".\.venv\Scripts\Activate.ps1"

if ($Install -or -not (Test-Path ".venv\.installed")) {
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	New-Item -ItemType File -Path ".venv\.installed" -Force | Out-Null
}

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
	Copy-Item ".env.example" ".env"
}

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000




