[Setup]
AppId={{44731029-D5ED-490E-BD1F-22F4BDC1F5AD}
AppName=Conversor
AppVersion=0.3.1
DefaultDirName={localappdata}\Programs\Conversor
DefaultGroupName=Conversor
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=Conversor-0.3.1-CLI-corrigida-Instalar
SetupIconFile=..\assets\conversor.ico
UninstallDisplayIcon={app}\Conversor.exe
Compression=zip/1
SolidCompression=no
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes
DiskSpanning=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\dist\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\engines\python\*"; DestDir: "{app}\engines\python"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,__pycache__\*"
Source: "..\engines\7zip\*"; DestDir: "{app}\engines\7zip"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.msi"
Source: "..\engines\imagemagick\*"; DestDir: "{app}\engines\imagemagick"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\engines\ffmpeg\*"; DestDir: "{app}\engines\ffmpeg"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\engines\libreoffice\*"; DestDir: "{app}\engines\libreoffice"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.msi"
Source: "..\engines\ghostscript\*"; DestDir: "{app}\engines\ghostscript"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\engines\calibre-msi\*"; DestDir: "{app}\engines\calibre-msi"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.msi"
Source: "..\engines\pandoc\*"; DestDir: "{app}\engines\pandoc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\engines\oda\*"; DestDir: "{app}\engines\oda"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.msi"
Source: "..\engines\deno\*"; DestDir: "{app}\engines\deno"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\VALIDACAO.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\RELATORIO-TESTES-20261026.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD-PARTY-NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\*.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Conversor"; Filename: "{app}\Conversor.exe"; WorkingDir: "{app}"
Name: "{userprograms}\Conversor"; Filename: "{app}\Conversor.exe"; WorkingDir: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Conversor"; ValueData: """{app}\Conversor.exe"" --background"; Flags: uninsdeletevalue; Check: ShouldStartWithWindows

[Run]
Filename: "{app}\Conversor.exe"; Description: "Abrir o Conversor"; Flags: nowait postinstall skipifsilent

[Code]
function ShouldStartWithWindows: Boolean;
var Config: AnsiString;
begin
  Result := True;
  if LoadStringFromFile(ExpandConstant('{localappdata}\Conversor\configuracoes.json'), Config) then
    Result := Pos('"StartWithWindows": false', String(Config)) = 0;
end;
