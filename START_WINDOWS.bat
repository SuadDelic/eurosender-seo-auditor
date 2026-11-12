@echo off
cd /d "%~dp0"
echo === Eurosender SEO Auditor ===
where py >nul 2>nul
if errorlevel 1 (
 echo Python Launcher not found. Install Python 3.12 from python.org.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe (
 echo Creating Python virtual environment...
 py -m venv .venv
 if errorlevel 1 ( echo Failed to create environment. & pause & exit /b 1 )
)
echo Installing required packages (first run may take a while)...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 ( echo Installation failed. & pause & exit /b 1 )
echo Launching Streamlit. Open the local URL shown below.
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
pause
