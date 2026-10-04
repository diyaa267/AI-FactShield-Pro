@echo off
cd /d "%~dp0"
echo This launcher is for optional ML retraining only.
echo It downloads public research datasets and is NOT required for Live News.
echo.
if not exist venv\Scripts\python.exe (
  py -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python scripts\train_large_model.py
pause
