param([int]$Port = 8501)

$ErrorActionPreference = 'Stop'
$speechPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $speechPython)) {
    throw 'Prepare the Python 3.12 speech environment first. See CONVERSATION.md.'
}
$env:HF_HOME = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\out\huggingface'))
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME 'hub'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
& $speechPython -m streamlit run (Join-Path $PSScriptRoot 'speech_webrtc.py') `
    --server.address 127.0.0.1 --server.port $Port --browser.gatherUsageStats false
exit $LASTEXITCODE
