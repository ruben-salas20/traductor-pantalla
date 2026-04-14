Dim fso, dir, pythonw, script
Set fso = CreateObject("Scripting.FileSystemObject")
dir     = fso.GetParentFolderName(WScript.ScriptFullPath)
pythonw = "C:\Users\ruben\AppData\Local\Programs\Python\Python314\pythonw.exe"
script  = dir & "\main.py"
CreateObject("WScript.Shell").Run """" & pythonw & """ """ & script & """", 0, False
