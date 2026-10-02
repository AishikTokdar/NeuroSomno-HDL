# Software verification; optional arguments are forwarded to the Python runner.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& python scripts/verify_project.py @args
exit $LASTEXITCODE
