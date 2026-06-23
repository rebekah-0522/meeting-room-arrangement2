Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d ""c:\Users\RECKS\Desktop\转正报告啊\Meeting Room Arrangement1"" && python server/app.py", 0, False