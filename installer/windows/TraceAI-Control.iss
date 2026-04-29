#define MyAppName "TraceAI Control"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "TraceAI Control"
#define MyAppExeName "TraceAI-Control.exe"
#define MyAppSourceDir "..\\..\\dist\\TraceAI-Control"

[Setup]
AppId={{8A75D8DA-8F5A-4E54-8C4A-TRACEAICONTROL}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\TraceAI Control
DefaultGroupName=TraceAI Control
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=TraceAI-Control-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TraceAI Control"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\TraceAI Control"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch TraceAI Control"; Flags: nowait postinstall skipifsilent
