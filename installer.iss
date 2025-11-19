; ScreenBlur Inno Setup Script
; 화면 가리개 애플리케이션 설치 프로그램

#define MyAppName "ScreenBlur"
#define MyAppPublisher "ScreenBlur Team"
#define MyAppURL "https://github.com/lsh930309/ScreenBlur"
#define MyAppExeName "ScreenBlur.exe"

[Setup]
; 앱 정보
AppId={{A5F5E3C1-9B2D-4E8A-A1C3-D4E5F6A7B8C9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; 출력 파일 설정
OutputDir={#SourcePath}\release
OutputBaseFilename=screenblur_v{#MyAppVersion}_setup
; 압축 설정
Compression=lzma2/max
SolidCompression=yes
; Windows 버전 요구사항
MinVersion=10.0
; 아이콘
SetupIconFile={#SourcePath}\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; 권한
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; UI 설정
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startupicon"; Description: "시작 프로그램에 등록"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourcePath}\dist\{#MyAppName}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  UninstallString: String;
begin
  // 기존 버전이 설치되어 있는지 확인
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1',
    'UninstallString', UninstallString) then
  begin
    if MsgBox('이전 버전의 {#MyAppName}이(가) 설치되어 있습니다. 계속하려면 이전 버전을 제거해야 합니다. 제거하시겠습니까?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 이전 버전 제거 실행
      Exec(UninstallString, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      Result := True;
    end
    else
    begin
      Result := False;
    end;
  end
  else
  begin
    Result := True;
  end;
end;
