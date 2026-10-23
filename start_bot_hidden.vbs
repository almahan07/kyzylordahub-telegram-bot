Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strPath

exePath = Chr(34) & strPath & "\venv\Scripts\pythonw.exe" & Chr(34)
scriptPath = Chr(34) & strPath & "\main.py" & Chr(34)

WshShell.Run exePath & " " & scriptPath, 0, False
