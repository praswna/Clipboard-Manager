@echo off
cd /d "E:\claud\clipboard_saver"
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul
python clipboard_manager.py
