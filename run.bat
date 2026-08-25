@echo off
title CHIFIA — Chili Intelligent Farming with AI
color 0A
echo.
echo  ==============================================
echo    CHIFIA — AI Chili Disease Detector
echo  ==============================================
echo.

:: Find Python
set PYTHON=
for %%P in (python py python3) do (
  %%P --version >nul 2>&1 && set PYTHON=%%P && goto found_python
)
:: Check common install path
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
  set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
  goto found_python
)
echo  [ERROR] Python tidak ditemukan!
echo  Unduh dari: https://www.python.org/downloads/
pause & exit /b 1

:found_python
echo  [OK] Python ditemukan: %PYTHON%

:: Install deps if needed
%PYTHON% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo  [INFO] Menginstall dependencies...
  %PYTHON% -m pip install -r requirements.txt --timeout 120
)

:: Check model
echo.
if exist "model\best.pt" (
  echo  [MODEL] ✅ model\best.pt ditemukan — Mode: YOLOv26 REAL
) else (
  echo  [MODEL] 🎭 model\best.pt tidak ada — Mode: DEMO
  echo  Letakkan file best.pt di folder model\ untuk deteksi nyata
)

echo.
echo  [START] Menjalankan server di http://localhost:5000
echo  Tekan Ctrl+C untuk berhenti
echo.
%PYTHON% app.py
pause
