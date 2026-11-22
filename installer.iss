; ============================================================================
;  A Última Vigília - script do instalador (Inno Setup 6.3 ou superior)
;  Compile com:  ISCC installer.iss      (ou abra no Inno Setup Compiler e F9)
;  Pré-requisito: rodar build.bat antes (gera dist\*.exe)
; ============================================================================
#define NomeApp "A Última Vigília"
#define VersaoApp "1.0.0"
#define ExeGui "UltimaVigilia.exe"
#define ExeCmd "UltimaVigilia-CMD.exe"

[Setup]
AppId={{3E5C9A41-7B2D-4F86-9C1A-D84B6E02F7A5}
AppName={#NomeApp}
AppVersion={#VersaoApp}
AppPublisher=A Última Vigília
DefaultDirName={autopf}\UltimaVigilia
DefaultGroupName={#NomeApp}
DisableProgramGroupPage=yes
OutputDir=instalador
OutputBaseFilename=UltimaVigilia-Instalador-{#VersaoApp}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Instala por usuário por padrão; o assistente oferece instalar para todos (Arquivos de Programas).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#ExeGui}
; Os saves ficam em %APPDATA%\UltimaVigilia e NÃO são tocados por atualização ou desinstalação.

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked
Name: "desktopiconcmd"; Description: "Criar atalho da versão de terminal na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "dist\{#ExeGui}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#ExeCmd}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#NomeApp}"; Filename: "{app}\{#ExeGui}"
Name: "{autoprograms}\{#NomeApp} (Terminal)"; Filename: "{app}\{#ExeCmd}"
Name: "{autodesktop}\{#NomeApp}"; Filename: "{app}\{#ExeGui}"; Tasks: desktopicon
Name: "{autodesktop}\{#NomeApp} (Terminal)"; Filename: "{app}\{#ExeCmd}"; Tasks: desktopiconcmd

[Run]
Filename: "{app}\{#ExeGui}"; Description: "Iniciar {#NomeApp}"; Flags: nowait postinstall skipifsilent
