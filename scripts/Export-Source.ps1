param(
    [string]$Root = (Split-Path $PSScriptRoot -Parent),
    [string]$Output = ''
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path
if (-not $Output) { $Output = Join-Path $Root 'dist\Conversor-0.3.1-Codigo-fonte.zip' }
if (Test-Path -LiteralPath $Output) { throw 'O ZIP já existe. Escolha outro caminho com -Output.' }
New-Item -ItemType Directory -Path (Split-Path $Output -Parent) -Force | Out-Null

# Use an allowlist so engines, personal state and downloaded samples cannot slip in.
$rootNames = @('.editorconfig', '.gitignore', 'engines.json', 'README.md',
    'VALIDACAO.md', 'RELATORIO-TESTES-20261026.md', 'THIRD-PARTY-NOTICES.md',
    'LICENSE', 'LICENSING.md', 'CHANGELOG.md', 'CONTRIBUTING.md')
$files = @(Get-ChildItem -LiteralPath $Root -File | Where-Object {
    $_.Extension -in @('.cs', '.xaml', '.csproj', '.manifest', '.cmd') -or
    $_.Name -in $rootNames -or $_.Name -like 'requirements*.txt'
})
foreach ($directory in @('Configuration', 'Conversion', 'Features', 'Infrastructure',
    'worker', 'scripts', 'installer', 'docs', 'assets', 'cli', 'tests')) {
    $files += Get-ChildItem -LiteralPath (Join-Path $Root $directory) -Recurse -File |
        Where-Object {
            $relative = [IO.Path]::GetRelativePath($Root, $_.FullName)
            $relative -notmatch '(^|[\\/])(bin|obj|results|fixtures|__pycache__|gesto-[^\\/]+)([\\/]|$)' -and
            $_.Extension -in @('.cs', '.csproj', '.py', '.ps1', '.iss', '.md', '.ico', '.png', '.svg')
        }
}

$archive = [IO.Compression.ZipFile]::Open($Output, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in $files | Sort-Object FullName -Unique) {
        $entryName = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\', '/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $entryName, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
}
finally { $archive.Dispose() }
Get-Item -LiteralPath $Output | Select-Object FullName, Length
