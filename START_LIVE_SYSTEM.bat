@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Creating virtual environment...
  py -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if not exist .env (
  echo.
  echo .env not found. Google News RSS and GDELT can still be used without API keys.
  echo Copy .env.example to .env and add API keys for additional live providers.
)
echo.
echo Starting AI FactShield Pro LIVE Internet News Verification...
echo Live articles are fetched from the Internet at request time.
echo No dataset download or demo evidence is required to open Live News.
echo.
python app.py
pause
