param([string]$Root = (Split-Path $PSScriptRoot -Parent))

$ErrorActionPreference = 'Stop'
$python = Join-Path $Root 'engines\python\python.exe'
$packages = Join-Path $Root 'engines\python\Lib\site-packages'
$downloads = Join-Path $Root 'downloads'
$runtime = Join-Path $Root 'engines\deno'
$manifestPath = Join-Path $Root 'engines.json'
$ytDlpVersion = '2026.10.21'
$denoVersion = '2.9.8'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Prepare o Python privado com Prepare-Engines.ps1 primeiro.'
}

New-Item -ItemType Directory -Path $downloads, $runtime -Force | Out-Null
rtk uv pip install --python $python --target $packages "yt-dlp[default,curl-cffi]==$ytDlpVersion"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar yt-dlp.' }

$asset = 'deno-x86_64-pc-windows-msvc.zip'
$source = "https://github.com/denoland/deno/releases/download/v$denoVersion/$asset"
$archive = Join-Path $downloads "deno-$denoVersion.zip"
if (-not (Test-Path -LiteralPath $archive)) { Invoke-WebRequest $source -OutFile $archive }
$checksumText = [string](Invoke-RestMethod "$source.sha256sum")
$checksum = [regex]::Match($checksumText, '\b[0-9a-fA-F]{64}\b').Value
if (-not $checksum) { throw 'Checksum oficial do Deno não foi encontrado.' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $checksum) {
    throw 'O pacote Deno não corresponde ao hash oficial.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $runtime -Force

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
$components = @{
    ytdlp = @{ path='engines\python\Lib\site-packages\yt_dlp\__init__.py'; source="https://pypi.org/project/yt-dlp/$ytDlpVersion/"; version=$ytDlpVersion }
    deno = @{ path='engines\deno\deno.exe'; source=$source; version=$denoVersion }
}
foreach ($name in $components.Keys) {
    $entry = $components[$name]
    $entry['sha256'] = (Get-FileHash -LiteralPath (Join-Path $Root $entry.path) -Algorithm SHA256).Hash
    $entry['preparedAt'] = (Get-Date).ToString('o')
    $manifest[$name] = $entry
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output 'yt-dlp e Deno preparados. Nenhum componente será baixado ao iniciar uma tarefa.'
