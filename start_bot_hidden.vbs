Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory
WshShell.Run "cmd /c """ & strPath & "\venv\Scripts\python.exe"" """ & strPath & "\main.py""", 0, False
