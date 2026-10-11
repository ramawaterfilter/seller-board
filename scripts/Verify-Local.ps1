$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program exited with code $LASTEXITCODE."
    }
}

$settingNames = @('UV_CACHE_DIR', 'RCI_ENV', 'RCI_DATABASE_URL', 'RCI_REDIS_URL',
                  'RCI_TEST_DATABASE_URL', 'PYTHONUTF8', 'PYTHONIOENCODING')
$previousSettings = @{}
foreach ($name in $settingNames) {
    $previousSettings[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

try {
    $env:UV_CACHE_DIR = Join-Path $projectRoot '.tmp/uv-cache'
    $env:RCI_ENV = 'local'
    $env:RCI_DATABASE_URL = 'postgresql+psycopg://rci_local:synthetic-local-only@127.0.0.1:5432/rci_local'
    $env:RCI_REDIS_URL = 'redis://127.0.0.1:6379/0'
    $env:RCI_TEST_DATABASE_URL = 'postgresql+psycopg://rci_local:synthetic-local-only@127.0.0.1:5432/rci_test_foundation'
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'

    Invoke-Checked 'docker' @('compose', 'up', '-d', '--wait', 'postgres', 'redis')
    Invoke-Checked 'uv' @('sync', '--locked')
    Invoke-Checked 'uv' @('run', 'alembic', '-c', 'api/alembic.ini', 'upgrade', 'head')

    $exists = & docker compose exec -T postgres psql -U rci_local -d postgres -tAc `
        "SELECT 1 FROM pg_database WHERE datname = 'rci_test_foundation'"
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect local test database.' }
    if (($exists -join '').Trim() -ne '1') {
        Invoke-Checked 'docker' @('compose', 'exec', '-T', 'postgres', 'createdb',
                                  '-U', 'rci_local', 'rci_test_foundation')
    }
    Invoke-Checked 'uv' @('run', 'pytest', '-q')
    Invoke-Checked 'uv' @('run', 'ruff', 'check', 'api/src', 'api/tests', 'api/alembic')
    Invoke-Checked 'uv' @('run', 'alembic', '-c', 'api/alembic.ini', 'heads')
    Write-Output 'Local migration and checks completed. Containers remain running.'
}
finally {
    foreach ($name in $settingNames) {
        [Environment]::SetEnvironmentVariable($name, $previousSettings[$name], 'Process')
    }
    Pop-Location
}
