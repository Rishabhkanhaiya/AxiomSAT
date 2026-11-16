@echo off
title AxiomSAT Dedicated Web Panel
color 09
cd /d "C:\Users\Rishabh_Joshi\Downloads\dm-course [project]"

echo ===============================================================================
echo          AxiomSAT ⚡ Formal Methods and Algorithmic Graph Theory
echo ===============================================================================
echo   Course: Discrete Mathematics  ^|  Faculty Guide: Prof. Shilpa Katikar
echo   Team:   Rishabh, Ujjwal, Shubham, Harshad (VIT Pune)
echo ===============================================================================
echo.
echo   [+] Launching Dedicated Web Panel...
echo   [+] Opening http://localhost:8501 in your browser...
echo.

set "PYTHON_CMD=C:\Users\Rishabh_Joshi\AppData\Local\Programs\Python\Python311\python.exe"
if not exist "%PYTHON_CMD%" (
    set "PYTHON_CMD=python"
)

:: Start browser directly
start "" "http://localhost:8501"

:: Launch Streamlit web app server
"%PYTHON_CMD%" -m streamlit run web\app.py --server.port 8501 --server.headless false

pause
