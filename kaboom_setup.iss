; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{YOUR-GUID-HERE}}
AppName=Kaboom
AppVersion=1.0
DefaultDirName={pf}\Kaboom
DefaultGroupName=Kaboom
UninstallDisplayIcon={app}\Kaboom.exe
OutputDir=.
OutputBaseFilename=kaboom-setup-1.O
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "Kaboom.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Client\images\bombe-icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Kaboom"; Filename: "{app}\Kaboom.exe"
Name: "{group}\{cm:UninstallProgram,Kaboom}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Kaboom"; Filename: "{app}\Kaboom.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Kaboom"; Filename: "{app}\Kaboom.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\Kaboom.exe"; Description: "{cm:LaunchProgram,Kaboom}"; Flags: nowait postinstall skipifsilent

[Code]
function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
  PythonVersion: string;
  TempFileName: string;
  PythonOutput: TStringList;
begin
  Result := False;
  TempFileName := ExpandConstant('{tmp}\python_version.txt');
  PythonOutput := TStringList.Create();
  try
    // Check if 'python --version' returns a valid Python 3 version
    if Exec('cmd.exe', '/C python --version > ' + TempFileName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if FileExists(TempFileName) then
      begin
        PythonOutput.LoadFromFile(TempFileName);
        PythonVersion := PythonOutput.Text;
        if Pos('Python 3', PythonVersion) = 1 then
        begin
          Result := True;
          Exit;
        end;
      end;
    end;

    // Check if 'python3 --version' returns a valid Python 3 version
    if Exec('cmd.exe', '/C python3 --version > ' + TempFileName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if FileExists(TempFileName) then
      begin
        PythonOutput.LoadFromFile(TempFileName);
        PythonVersion := PythonOutput.Text;
        if Pos('Python 3', PythonVersion) = 1 then
        begin
          Result := True;
          Exit;
        end;
      end;
    end;

    // If neither command returns a valid Python 3 version, show an error message
    MsgBox('Python 3.0 or higher is not installed. Please install Python 3.0 or higher before proceeding.', mbError, MB_OK);
  finally
    PythonOutput.Free();
    if FileExists(TempFileName) then
      DeleteFile(TempFileName);
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := IsPythonInstalled();
end;