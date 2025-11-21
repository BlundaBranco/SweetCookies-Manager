@echo off
echo Iniciando SweetCookies Manager...
call venv\Scripts\activate
start http://127.0.0.1:5000
python app.py
pause