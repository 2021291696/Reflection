$installDir = "$env:LOCALAPPDATA\Reflection"
$exePath = "$installDir\Reflection.exe"

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Reflection.lnk')
$lnk.TargetPath = $exePath
$lnk.WorkingDirectory = $installDir
$lnk.Description = 'Reflection'
$lnk.Save()

$smDir = [Environment]::GetFolderPath('StartMenu') + '\Programs\Reflection'
New-Item -ItemType Directory -Force -Path $smDir | Out-Null
$smlnk = $ws.CreateShortcut($smDir + '\Reflection.lnk')
$smlnk.TargetPath = $exePath
$smlnk.WorkingDirectory = $installDir
$smlnk.Description = 'Reflection'
$smlnk.Save()