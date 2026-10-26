param(
    [string]$Root = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path
$appOutput = Join-Path $Root 'dist\app'
$cliOutput = Join-Path $Root 'dist\cli'
$cache = Join-Path $Root 'dist\cli-verified'
$manifestPath = Join-Path $cache 'manifest.json'
$launcherFiles = @('conversor-cli.exe', 'conversor-cli.dll',
    'conversor-cli.deps.json', 'conversor-cli.runtimeconfig.json')
$sourceFiles = @('cli\CliEntry.cs', 'cli\Conversor.Cli.csproj')

# The forwarding launcher does not need rebuilding for a change to the GUI.
# This cache records functional validation; it does not grant Windows trust.
$canReuse = $false
if (Test-Path -LiteralPath $manifestPath) {
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
        $canReuse = $manifest.schema -eq 1
        foreach ($file in $sourceFiles) {
            $canReuse = $canReuse -and
                ((Get-FileHash -LiteralPath (Join-Path $Root $file)).Hash -eq $manifest.sources[$file])
        }
        foreach ($file in $launcherFiles) {
            $path = Join-Path $cache $file
            $canReuse = $canReuse -and (Test-Path -LiteralPath $path) -and
                ((Get-FileHash -LiteralPath $path).Hash -eq $manifest.files[$file])
        }
    }
    catch { $canReuse = $false }
}

if ($canReuse) {
    foreach ($destination in @($appOutput, $cliOutput)) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        foreach ($file in $launcherFiles) {
            Copy-Item -LiteralPath (Join-Path $cache $file) -Destination $destination -Force
        }
    }
    Write-Host 'Lançador CLI preservado: código e hashes conferem com a cópia validada.'
}
else {
    $env:DOTNET_CLI_HOME = Join-Path $Root '.build-home'
    $env:NUGET_PACKAGES = Join-Path $Root '.nuget'
    rtk dotnet publish (Join-Path $Root 'cli\Conversor.Cli.csproj') -c Release -r win-x64 --self-contained true -o $cliOutput --nologo
    if ($LASTEXITCODE -ne 0) { throw 'Publicação da linha de comando falhou.' }
    Get-ChildItem -LiteralPath $cliOutput -File | Copy-Item -Destination $appOutput -Force
}

# Confirm that the launcher can still call the current application's public API.
& (Join-Path $appOutput 'conversor-cli.exe') --help
if ($LASTEXITCODE -ne 0) {
    throw 'A CLI não passou na verificação de execução. Revise o bloqueio e a assinatura; não foi criada uma exceção de segurança.'
}
