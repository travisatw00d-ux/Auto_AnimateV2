@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  AccuRIG -> Mixamo Bone Name Converter
::  Drag-drop your AccuRIG .fbx to get a Mixamo-compatible version
:: ============================================================

set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
set "SCRIPT=%~dp0scripts\export_for_mixamo.py"

if "%~1"=="" (
    echo.
    echo  Drag-drop an AccuRIG .fbx file onto this batch file.
    echo.
    echo  It will rename bones to Mixamo names and save a copy
    echo  with "_Mixamo" suffix next to the original.
    echo.
    pause
    exit /b
)

set "INPUT=%~1"

if not exist "!INPUT!" (
    echo  ERROR: File not found: !INPUT!
    pause & exit /b 1
)

for %%f in ("!INPUT!") do set "NAME=%%~nf"
for %%f in ("!INPUT!") do set "DIR=%%~dpf"
set "OUTPUT=!DIR!!NAME!_Mixamo.fbx"

echo.
echo  Converting: !INPUT!
echo  Output:     !OUTPUT!
echo.
echo  Running bone rename...

"%BLENDER%" --background --python "%SCRIPT%" -- "!INPUT!" "!OUTPUT!" 2>&1

if errorlevel 1 (
    echo.
    echo  ERROR: Conversion failed.
    pause & exit /b 1
)

echo.
echo  Done! Upload this file to Mixamo.com
echo    Use "map existing skeleton" option
echo.
echo  File: !OUTPUT!
echo.
pause
exit /b 0
