param([string]$Root=(Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$downloadDir=Join-Path $Root 'downloads'
$engineDir=Join-Path $Root 'engines'
New-Item -ItemType Directory -Force -Path $downloadDir,$engineDir | Out-Null
$manifestPath=Join-Path $Root 'engines.json'
$script:manifest=@{}
if(Test-Path $manifestPath) { $script:manifest=Get-Content $manifestPath -Raw | ConvertFrom-Json -AsHashtable }
# A source checkout includes the manifest, but not the private engine binaries.
foreach ($name in @($script:manifest.Keys)) {
 $component = $script:manifest[$name]
 if (!$component.path -or !(Test-Path -LiteralPath (Join-Path $Root $component.path) -PathType Leaf)) {
  $script:manifest.Remove($name)
 }
}
function Save-Manifest { $script:manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8 }
function Fetch([string]$Url,[string]$Name) {
 $dest=Join-Path $downloadDir $Name
 if(!(Test-Path $dest)) { Write-Host "Baixando $Name"; Invoke-WebRequest -Uri $Url -OutFile ($dest+'.part') -TimeoutSec 1800; Move-Item -LiteralPath ($dest+'.part') -Destination $dest }
 return $dest
}
function Register([string]$Name,[string]$Path,[string]$Url,[string]$Archive) {
 $script:manifest[$Name]=@{path=[IO.Path]::GetRelativePath($Root,$Path);source=$Url;sha256=(Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash;preparedAt=[DateTimeOffset]::Now.ToString('O')}
 Save-Manifest
 Write-Output "Preparado: $Name"
}
function Extract-Msi([string]$File,[string]$Destination) {
 New-Item -ItemType Directory -Force -Path $Destination | Out-Null
 $p=Start-Process msiexec.exe -ArgumentList @('/a',('"'+$File+'"'),'/qn',('TARGETDIR="'+$Destination+'"'),'/L*v',('"'+$Destination+'.log"')) -WindowStyle Hidden -Wait -PassThru
 if($p.ExitCode -notin @(0,3010)) { throw "Extração MSI falhou: $($p.ExitCode) ($Destination.log)" }
}
function Find-Exe([string]$Dir,[string]$Name) { $found=Get-ChildItem -LiteralPath $Dir -Filter $Name -Recurse -File | Select-Object -First 1; if(!$found){throw "$Name não encontrado em $Dir"}; return $found.FullName }
function Github([string]$Repo) { return Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers @{'User-Agent'='Conversor-local-setup'} }

# Administrative extraction does not register 7-Zip or LibreOffice on the computer.
if(!$manifest.ContainsKey('sevenzip')) {
 $release=Github 'ip7z/7zip'; $asset=$release.assets | Where-Object name -Match '^7z\d+-x64\.msi$' | Select-Object -First 1
 $archive=Fetch $asset.browser_download_url $asset.name
 $dest=Join-Path $engineDir '7zip'; Extract-Msi $archive $dest
 Register 'sevenzip' (Find-Exe $dest '7z.exe') $asset.browser_download_url $archive
}
$seven=Join-Path $Root $manifest['sevenzip']['path']
function Expand-Seven([string]$File,[string]$Dest) { & $seven x $File ('-o'+$Dest) -y -bso0 -bsp0; if($LASTEXITCODE -ne 0){throw "Extração falhou: $File"} }

if(!$manifest.ContainsKey('python')) {
 $url='https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'; $archive=Fetch $url 'python-3.12.10-embed-amd64.zip'
 $dest=Join-Path $engineDir 'python'; Expand-Archive -LiteralPath $archive -DestinationPath $dest -Force
 @('python312.zip','.','Lib\site-packages','import site') | Set-Content -LiteralPath (Join-Path $dest 'python312._pth') -Encoding ascii
 & uv pip install --python (Join-Path $dest 'python.exe') --target (Join-Path $dest 'Lib\site-packages') 'pypdf==6.1.1' 'pypdfium2==4.30.0' 'pillow==11.3.0' 'fonttools[woff]==4.60.1' 'ezdxf==1.4.3' 'matplotlib==3.10.7' 'pymupdf==1.26.5' 'python-docx==1.2.0' 'openpyxl==3.1.5' 'python-pptx==1.0.2' 'pytest==8.4.2'
 if($LASTEXITCODE -ne 0) { throw 'Instalação dos componentes Python falhou' }
 Register 'python' (Join-Path $dest 'python.exe') $url $archive
}
if(!$manifest.ContainsKey('magick')) {
 $release=Github 'ImageMagick/ImageMagick'; $asset=$release.assets | Where-Object name -Match 'portable-Q16-x64\.7z$' | Select-Object -First 1
 if(!$asset){throw 'Pacote portátil ImageMagick não encontrado'}
 $archive=Fetch $asset.browser_download_url $asset.name; $dest=Join-Path $engineDir 'imagemagick'; Expand-Seven $archive $dest
 Register 'magick' (Find-Exe $dest 'magick.exe') $asset.browser_download_url $archive
}
if(!$manifest.ContainsKey('ffmpeg')) {
 $url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $archive=Fetch $url 'ffmpeg-release-essentials.zip'
 $dest=Join-Path $engineDir 'ffmpeg'; Expand-Archive -LiteralPath $archive -DestinationPath $dest -Force
 Register 'ffmpeg' (Find-Exe $dest 'ffmpeg.exe') $url $archive
}
if(!$manifest.ContainsKey('libreoffice')) {
 $url='https://download.documentfoundation.org/libreoffice/stable/26.8.1/win/x86_64/LibreOffice_26.8.1_Win_x86-64.msi'; $archive=Fetch $url 'LibreOffice_26.8.1_Win_x86-64.msi'
 $dest=Join-Path $engineDir 'libreoffice'; Extract-Msi $archive $dest
 Register 'libreoffice' (Find-Exe $dest 'soffice.exe') $url $archive
}
if(!$manifest.ContainsKey('ghostscript')) {
 $release=Github 'ArtifexSoftware/ghostpdl-downloads'; $asset=$release.assets | Where-Object name -Match '^gs.*w64\.exe$' | Select-Object -First 1
 $archive=Fetch $asset.browser_download_url $asset.name; $dest=Join-Path $engineDir 'ghostscript'; Expand-Seven $archive $dest
 Register 'ghostscript' (Find-Exe $dest 'gswin64c.exe') $asset.browser_download_url $archive
}
if(!$manifest.ContainsKey('pandoc')) {
 $release=Github 'jgm/pandoc'; $asset=$release.assets | Where-Object name -Match 'windows-x86_64\.zip$' | Select-Object -First 1
 $archive=Fetch $asset.browser_download_url $asset.name; $dest=Join-Path $engineDir 'pandoc'; Expand-Archive -LiteralPath $archive -DestinationPath $dest -Force
 Register 'pandoc' (Find-Exe $dest 'pandoc.exe') $asset.browser_download_url $archive
}
if(!$manifest.ContainsKey('calibre')) {
 $release=Github 'kovidgoyal/calibre'; $asset=$release.assets | Where-Object name -Match '^calibre-64bit-.*\.msi$' | Select-Object -First 1
 if(!$asset){throw 'Pacote MSI oficial do calibre não encontrado'}
 $url=$asset.browser_download_url;$name=$asset.name
 $archive=Fetch $url $name; $dest=Join-Path $engineDir 'calibre-msi';Extract-Msi $archive $dest
 Register 'calibre' (Find-Exe $dest 'ebook-convert.exe') $url $archive
}
if(!$manifest.ContainsKey('oda')) {
 $url='https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi';$archive=Fetch $url 'ODAFileConverter-x64.msi'
 $dest=Join-Path $engineDir 'oda';Extract-Msi $archive $dest
 Register 'oda' (Find-Exe $dest 'ODAFileConverter.exe') $url $archive
}
& (Join-Path $PSScriptRoot 'Prepare-Downloader.ps1') -Root $Root
Write-Output 'Motores locais e componentes de download preparados.'
