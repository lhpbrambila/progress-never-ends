; ============================================================================
;  Crônicas de Cinzas - script do instalador (Inno Setup 6.3 ou superior)
;  Compile com:  ISCC installer.iss      (ou abra no Inno Setup Compiler e F9)
;  Pré-requisito: rodar build.bat antes (gera dist\*.exe)
; ============================================================================
#define NomeApp "Crônicas de Cinzas"
#define VersaoApp "1.0.0"
#define ExeGui "CronicasDeCinzas.exe"
#define ExeCmd "CronicasDeCinzas-CMD.exe"

[Setup]
AppId={{7ABB65CD-8299-462C-A55E-849856A8F1BC}
AppName={#NomeApp}
AppVersion={#VersaoApp}
AppPublisher=Crônicas de Cinzas
DefaultDirName={autopf}\CronicasDeCinzas
DefaultGroupName={#NomeApp}
DisableProgramGroupPage=yes
OutputDir=instalador
OutputBaseFilename=CronicasDeCinzas-Instalador-{#VersaoApp}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Instala por usuário por padrão; o assistente oferece instalar para todos (Arquivos de Programas).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#ExeGui}
; Os saves ficam em %APPDATA%\CronicasDeCinzas e NÃO são tocados por atualização ou desinstalação.

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
