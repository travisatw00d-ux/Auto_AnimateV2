@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  FBX to GLB Converter
::  Drag-drop a .fbx file to convert it to .glb
:: ============================================================

set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
set "SCRIPT=%~dp0fbx_to_glb.py"

if "%~1"=="" (
    echo.
    echo  Drag-drop a .fbx file onto this batch file.
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
set "OUTPUT=!DIR!!NAME!.glb"

echo.
echo  Converting: !INPUT!
echo  Output:     !OUTPUT!
echo.

"%BLENDER%" --background --python "%SCRIPT%" -- --fbx "!INPUT!" --output "!OUTPUT!" 2>&1

if errorlevel 1 (
    echo.
    echo  ERROR: Conversion failed.
    pause & exit /b 1
)

echo.
echo  Done: !OUTPUT!
echo.
pause
exit /b 0
