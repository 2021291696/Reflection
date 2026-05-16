Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

installDir = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Reflection"
sourceExe = fso.GetParentFolderName(WScript.ScriptFullName) & "\Reflection.exe"

' Copy exe
If Not fso.FolderExists(installDir) Then fso.CreateFolder installDir
fso.CopyFile sourceExe, installDir & "\Reflection.exe", True

' Desktop shortcut
Set lnk = shell.CreateShortcut(shell.SpecialFolders("Desktop") & "\Reflection.lnk")
lnk.TargetPath = installDir & "\Reflection.exe"
lnk.WorkingDirectory = installDir
lnk.Description = "Reflection"
lnk.Save()

' Start Menu shortcut
smDir = shell.SpecialFolders("StartMenu") & "\Programs\Reflection"
If Not fso.FolderExists(smDir) Then fso.CreateFolder smDir
Set smLnk = shell.CreateShortcut(smDir & "\Reflection.lnk")
smLnk.TargetPath = installDir & "\Reflection.exe"
smLnk.WorkingDirectory = installDir
smLnk.Description = "Reflection"
smLnk.Save()

MsgBox "Reflection installed. Double-click [Reflection] on your desktop to start.", 64, "Reflection"
