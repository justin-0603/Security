' VBScript to safely launch capture.py in the background without spawning CMD window
Option Explicit

Dim objShell, objFSO, strScriptDir, strCommand

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get current directory where this VBScript resides
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Set working directory to the project folder to prevent path errors
objShell.CurrentDirectory = strScriptDir

' Check if capture.py exists in the folder
If Not objFSO.FileExists(strScriptDir & "\capture.py") Then
    MsgBox "Error: capture.py file not found in directory!", 16, "Execution Error"
    WScript.Quit
End If

' Launch capture.py using pythonw completely hidden
strCommand = "cmd.exe /c start /b pythonw """ & strScriptDir & "\capture.py"""
objShell.Run strCommand, 0, False

Set objShell = Nothing
Set objFSO = Nothing