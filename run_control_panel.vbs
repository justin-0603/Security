' VBScript to safely launch control_panel.py in the background without spawning CMD window
Option Explicit

Dim objShell, objFSO, strScriptDir, strPythonPath, strCommand

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get current directory where this VBScript resides
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Set working directory to the project folder to prevent path errors
objShell.CurrentDirectory = strScriptDir

' Check if control_panel.py exists in the folder
If Not objFSO.FileExists(strScriptDir & "\control_panel.py") Then
    MsgBox "Error: control_panel.py file not found in directory!", 16, "Execution Error"
    WScript.Quit
End If

' Launch control_panel.py using pythonw completely hidden
strCommand = "cmd.exe /c start /b pythonw """ & strScriptDir & "\control_panel.py"""
objShell.Run strCommand, 0, False

Set objShell = Nothing
Set objFSO = Nothing