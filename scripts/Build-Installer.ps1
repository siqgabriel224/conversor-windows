$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $root
$env:DOTNET_CLI_HOME=Join-Path $root '.build-home'
$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
$env:NUGET_PACKAGES=Join-Path $root '.nuget'
& (Join-Path $root 'engines\python\python.exe') (Join-Path $PSScriptRoot 'make_icon.py')
rtk dotnet publish Conversor.csproj -c Release -r win-x64 --self-contained true -o dist\app --nologo
if($LASTEXITCODE -ne 0){throw 'Publicação do aplicativo falhou'}
& (Join-Path $PSScriptRoot 'Publish-Cli.ps1') -Root $root
Copy-Item -LiteralPath (Join-Path $root 'engines.json') -Destination (Join-Path $root 'dist\app\engines.json') -Force
Copy-Item -LiteralPath (Join-Path $root 'conversor.cmd') -Destination (Join-Path $root 'dist\app\conversor.cmd') -Force
$compiler=Join-Path $root 'tools\InnoSetup\ISCC.exe'
if(!(Test-Path -LiteralPath $compiler)){
 $setup=Join-Path $root 'downloads\innosetup-7.1.0-x64.exe'
 if(!(Test-Path $setup)){Invoke-WebRequest 'https://github.com/jrsoftware/issrc/releases/download/is-7_1_0/innosetup-7.1.0-x64.exe' -OutFile $setup}
 $sig=Get-AuthenticodeSignature -LiteralPath $setup
 if($sig.Status -ne 'Valid'){throw 'Assinatura do instalador do compilador não validada'}
 $p=Start-Process -FilePath $setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER','/NOICONS',('/DIR="'+(Join-Path $root 'tools\InnoSetup')+'"')) -WindowStyle Hidden -Wait -PassThru
 if($p.ExitCode -ne 0){throw 'Preparação do compilador falhou'}
}
& $compiler /Q (Join-Path $root 'installer\Conversor.iss')
if($LASTEXITCODE -ne 0){throw 'Criação do instalador falhou'}
