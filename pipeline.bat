@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  Auto-Animate Pipeline
::  Works with any AccuRIG-rigged FBX/GLB model.
::  Per-model data stored in temp\<modelname>\
:: ============================================================

set "BLENDER=C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
set "SELF=%~dp0"
set "SCRIPTS=%SELF%scripts"
set "TEMP=%SELF%temp"
set "OUTPUT=%SELF%output"

if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "%OUTPUT%" mkdir "%OUTPUT%"

:MAIN_MENU
echo.
echo ============================================================
echo  AUTO-ANIMATE PIPELINE
echo ============================================================
echo.
echo  [1] Clear All And Start New
echo  [2] Add Animations (keep existing)
echo  [3] Manually Delete Animations
echo  [4] Clean Temp (delete temporary files for a model)
echo.
set /p MODE="  Choose (1, 2, 3, or 4): "

if "!MODE!"=="1" goto START_FRESH
if "!MODE!"=="2" goto ADD_MODE
if "!MODE!"=="3" goto DELETE_MODE
if "!MODE!"=="4" goto CLEAN_TEMP
echo  Invalid choice
pause & exit /b 1

:START_FRESH
:: Clean the entire temp (all models)
rd /s /q "%TEMP%" >nul 2>&1
mkdir "%TEMP%"
goto GET_MODEL

:ADD_MODE
echo.
echo  Using existing session data in temp\
echo.
goto GET_MODEL

:DELETE_MODE
echo.
echo ============================================================
echo  DELETE ANIMATIONS FROM GLB
echo ============================================================
echo.
echo  Drag a .glb file here and press Enter
echo.
set /p DELETE_INPUT="  Model: "
set "DELETE_INPUT=!DELETE_INPUT:"=!"

if not exist "!DELETE_INPUT!" (
    echo  ERROR: File not found
    pause & exit /b 1
)

for %%f in ("!DELETE_INPUT!") do set "DELETE_EXT=%%~xf"
if /i not "!DELETE_EXT!"==".glb" (
    echo  ERROR: Only .glb files are supported for deletion
    pause & exit /b 1
)

for %%f in ("!DELETE_INPUT!") do set "DELETE_FILE=%%~nf"
set "DELETE_KEY=!DELETE_FILE!"
for %%a in (!DELETE_KEY!) do set "DELETE_KEY=%%a"
set "DELETE_KEY=!DELETE_KEY: =_!"

:: Backup original if not already backed up
if not exist "%OUTPUT%\!DELETE_KEY!_original.glb" (
    copy /y "!DELETE_INPUT!" "%OUTPUT%\!DELETE_KEY!_original.glb" >nul
    echo  Original backed up to output\!DELETE_KEY!_original.glb
)

:: List animations via Blender
set "ANIM_LIST=%TEMP%\!DELETE_KEY!_anim_list.txt"
"%BLENDER%" --background --python "%SCRIPTS%\list_glb_animations.py" -- "!DELETE_INPUT!" "!ANIM_LIST!" 2>&1

echo.
echo  ============================================================
echo  Animations on !DELETE_FILE!:
echo  ============================================================
type "%ANIM_LIST%"
echo.

:: Check if any animations exist
set /p FIRST_LINE=<"%ANIM_LIST%"
if "!FIRST_LINE!"=="(none)" (
    echo  No animations to delete
    pause & goto MAIN_MENU
)

:: Prompt for indices
:DELETE_PROMPT
set /p DELETE_INDICES="  Which to delete? (comma-separated numbers, e.g. 1,3,5): "
if "!DELETE_INDICES!"=="" (
    echo  No indices entered ? returning to menu
    pause & goto MAIN_MENU
)

:: Run deletion via Blender
"%BLENDER%" --background --python "%SCRIPTS%\delete_glb_animations.py" -- "!DELETE_INPUT!" "!DELETE_INDICES!" 2>&1

if errorlevel 1 (
    echo.
    echo  ERROR: Deletion failed ? check indices and try again
    goto DELETE_PROMPT
)

echo.
echo  ============================================================
echo  DELETE COMPLETE
echo  ============================================================
echo.

del "%ANIM_LIST%" >nul 2>&1
echo.
goto MAIN_MENU

:CLEAN_TEMP
echo.
echo ============================================================
echo  CLEAN TEMP FILES
echo ============================================================
echo.
echo  Drag a .fbx or .glb file here and press Enter
echo  (this will delete all temporary files for this model)
echo.
set /p CLEAN_INPUT="  Model: "
set "CLEAN_INPUT=!CLEAN_INPUT:"=!"
if not exist "!CLEAN_INPUT!" (
    echo  ERROR: File not found
    pause & goto MAIN_MENU
)
for %%f in ("!CLEAN_INPUT!") do set "CLEAN_FILE=%%~nf"
set "CLEAN_KEY=!CLEAN_FILE!"
for %%a in (!CLEAN_KEY!) do set "CLEAN_KEY=%%a"
set "CLEAN_KEY=!CLEAN_KEY: =_!"
if exist "%TEMP%\!CLEAN_KEY!" (
    rd /s /q "%TEMP%\!CLEAN_KEY!" >nul 2>&1
    echo  Deleted temp files for: !CLEAN_KEY!
) else (
    echo  No temp files found for: !CLEAN_KEY!
)
echo.
goto MAIN_MENU

:GET_MODEL
echo ============================================================
echo  Select your AccuRIG model:
echo    Drag a .fbx or .glb file here and press Enter
echo.
set /p MODEL_INPUT="  Model: "
set "MODEL_INPUT=!MODEL_INPUT:"=!"

if not exist "!MODEL_INPUT!" (
    echo  ERROR: File not found
    pause & exit /b 1
)

for %%f in ("!MODEL_INPUT!") do set "MODEL_EXT=%%~xf"
for %%f in ("!MODEL_INPUT!") do set "MODEL_FILE=%%~nf"

:: Build model key (safe directory name)
set "MODEL_KEY=!MODEL_FILE!"
for %%a in (!MODEL_KEY!) do set "MODEL_KEY=%%a"
set "MODEL_KEY=!MODEL_KEY: =_!"

:: Per-model data directory
set "MODEL_DIR=%TEMP%\!MODEL_KEY!"
if not exist "!MODEL_DIR!" mkdir "!MODEL_DIR!"

:: Convert GLB to FBX if needed
if /i "!MODEL_EXT!"==".glb" (
    echo  Converting .glb to .fbx...
    set "MODEL_FBX=%TEMP%\!MODEL_KEY!.fbx"
    "%BLENDER%" --background --python "%SCRIPTS%\glb_to_fbx.py" -- "!MODEL_INPUT!" "!MODEL_FBX!" 2>&1
    if errorlevel 1 (echo  ERROR: GLB conversion failed & pause & exit /b 1)
) else (
    set "MODEL_FBX=!MODEL_INPUT!"
)

:: Per-model paths
set "CHAR_BLEND=!MODEL_DIR!\character.blend"
set "BASE_BLEND=!MODEL_DIR!\base.blend"
set "MASTER_BLEND=!MODEL_DIR!\master.blend"
:: Output GLB replaces the original (same dir, same base name)
set "OUTPUT_DIR=!MODEL_INPUT!"
for %%f in ("!MODEL_INPUT!") do set "OUTPUT_DIR=%%~dpf"
set "OUTPUT_GLB=%OUTPUT_DIR%!MODEL_KEY!.glb"

:: Backup original model before overwriting
if not exist "%OUTPUT%\!MODEL_KEY!_original.glb" (
    if exist "!MODEL_INPUT!" (
        copy /y "!MODEL_INPUT!" "%OUTPUT%\!MODEL_KEY!_original.glb" >nul
        echo  Original backed up to output\!MODEL_KEY!_original.glb
    )
)

:: Mode-specific setup
if "!MODE!"=="2" (
    :: Sync master with current GLB so manually-deleted animations don't resurface
    if exist "!MASTER_BLEND!" if exist "!OUTPUT_GLB!" (
        echo  Syncing master with current GLB...
        "%BLENDER%" --background --python "%SCRIPTS%\sync_master_from_glb.py" -- "!MASTER_BLEND!" "!OUTPUT_GLB!" 2>&1
    )
    if exist "!CHAR_BLEND!" goto ANIM_LOOP
    if exist "!MASTER_BLEND!" (
        echo  Restoring from existing master.blend...
        copy /y "!MASTER_BLEND!" "!CHAR_BLEND!" >nul
        goto ANIM_LOOP
    )
    echo  First run in add-mode - creating base from model...
    "%BLENDER%" --background --python "%SCRIPTS%\create_character_blend.py" -- "!MODEL_FBX!" "!BASE_BLEND!" 2>&1
    if errorlevel 1 (echo  ERROR: Failed to create base & pause & exit /b 1)
    echo  Transferring textures from model...
    "%BLENDER%" --background --python "%SCRIPTS%\transfer_model_textures.py" -- "!MODEL_FBX!" "!BASE_BLEND!" "!CHAR_BLEND!" 2>&1
    copy /y "!CHAR_BLEND!" "!MASTER_BLEND!" >nul
    :: Import existing animations from original GLB (if any) into master.blend
    if /i "!MODEL_EXT!"==".glb" (
        echo  Importing existing animations from original GLB...
        "%BLENDER%" --background --python "%SCRIPTS%\import_glb_animations.py" -- "!MODEL_INPUT!" "!MASTER_BLEND!" 2>&1
    )
    echo  Ready - add animations to this model
    goto ANIM_LOOP
)

:: Mode 1: clean start per-model
echo  Creating base from model...
"%BLENDER%" --background --python "%SCRIPTS%\create_character_blend.py" -- "!MODEL_FBX!" "!BASE_BLEND!" 2>&1
if errorlevel 1 (echo  ERROR: Failed to create base & pause & exit /b 1)
echo  Transferring textures from model...
"%BLENDER%" --background --python "%SCRIPTS%\transfer_model_textures.py" -- "!MODEL_FBX!" "!BASE_BLEND!" "!CHAR_BLEND!" 2>&1
copy /y "!CHAR_BLEND!" "!MASTER_BLEND!" >nul
echo  Base + textures ready for !MODEL_KEY!

:ANIM_LOOP
echo.
echo ============================================================
echo  ADD ANIMATION  ^(!MODEL_KEY!^)
echo ============================================================
echo.
echo  Drag a Mixamo .fbx or .bvh animation here:
echo  (or press Enter to finish)
echo.
set /p ANIM_INPUT="  Animation: "

if "!ANIM_INPUT!"=="" goto FINISH
set "ANIM_INPUT=!ANIM_INPUT:"=!"

if not exist "!ANIM_INPUT!" (
    echo  ERROR: File not found
    goto ANIM_LOOP
)

for %%f in ("!ANIM_INPUT!") do set "ANIM_EXT=%%~xf"
for %%f in ("!ANIM_INPUT!") do set "ANIM_NAME=%%~nf"

:: Clean intermediate BVH files
del "!MODEL_DIR!\character_bvh*.blend" >nul 2>&1
del "!MODEL_DIR!\character_bvh*.blend1" >nul 2>&1

:: ============================================================
:: Process animation
:: ============================================================

if /i "!ANIM_EXT!"==".fbx" (
    :: Mode 1: reset character from base before importing each animation
    if not "!MODE!"=="2" (
        copy /y "!BASE_BLEND!" "!CHAR_BLEND!" >nul
        echo  Transferring textures from model...
        "%BLENDER%" --background --python "%SCRIPTS%\transfer_model_textures.py" -- "!MODEL_FBX!" "!BASE_BLEND!" "!CHAR_BLEND!" 2>&1
    )
    echo  [Mixamo FBX] Importing animation...
    set "ANIM_OUTPUT=%OUTPUT%\!ANIM_NAME!.fbx"
    "%BLENDER%" --background "!CHAR_BLEND!" --python "%SCRIPTS%\import_mixamo_anim.py" -- "!CHAR_BLEND!" "!ANIM_INPUT!" "!ANIM_OUTPUT!" 2>&1
    if errorlevel 1 (echo  ERROR: Mixamo import failed & pause & exit /b 1)

) else if /i "!ANIM_EXT!"==".bvh" (
    set "BVH_WORK=!MODEL_DIR!\character_bvh.blend"
    copy /y "!BASE_BLEND!" "!BVH_WORK!" >nul
    echo  Transferring textures...
    "%BLENDER%" --background --python "%SCRIPTS%\transfer_model_textures.py" -- "!MODEL_FBX!" "!BASE_BLEND!" "!BVH_WORK!" 2>&1
    echo  [BVH detected] Running retargeter...
    set "ANIM_OUTPUT=%OUTPUT%\!ANIM_NAME!.fbx"
    "%BLENDER%" --background "!BVH_WORK!" --python "%SCRIPTS%\add_animation_bvh.py" -- "!BVH_WORK!" "!ANIM_INPUT!" "%OUTPUT%" 2>&1
    if errorlevel 1 (echo  ERROR: BVH retargeting failed & del "!BVH_WORK!" >nul 2>&1 & pause & exit /b 1)

    if exist "!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend" (
        if "!MODE!"=="2" (
            set "MERGE_SOURCE=!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend"
        ) else (
            copy /y "!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend" "!CHAR_BLEND!" >nul
            del "!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend" >nul 2>&1
        )
    ) else if exist "!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend1" (
        if "!MODE!"=="2" (
            set "MERGE_SOURCE=!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend1"
        ) else (
            copy /y "!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend1" "!CHAR_BLEND!" >nul
            del "!MODEL_DIR!\character_bvh_!ANIM_NAME!.blend1" >nul 2>&1
        )
    )
    del "!BVH_WORK!" >nul 2>&1

) else (
    echo  ERROR: Unsupported format. Use .fbx or .bvh
    goto ANIM_LOOP
)

:: Merge into master then export GLB
if exist "!MASTER_BLEND!" (
    del "!MASTER_BLEND!1" >nul 2>&1
    echo  Merging animation into master ^(!MODEL_KEY!^)...
    if defined MERGE_SOURCE (
        "%BLENDER%" --background --python "%SCRIPTS%\merge_action.py" -- "!MASTER_BLEND!" "!MERGE_SOURCE!" 2>&1
        del "!MERGE_SOURCE!" >nul 2>&1
        set "MERGE_SOURCE="
    ) else (
        "%BLENDER%" --background --python "%SCRIPTS%\merge_action.py" -- "!MASTER_BLEND!" "!CHAR_BLEND!" 2>&1
    )
) else (
    copy /y "!CHAR_BLEND!" "!MASTER_BLEND!" >nul
)
echo  Exporting GLB...
"%BLENDER%" --background --python "%SCRIPTS%\export_glb.py" -- "!MASTER_BLEND!" "!OUTPUT_GLB!" 2>&1
if errorlevel 1 (echo  ERROR: GLB export failed & pause & exit /b 1)
ping -n 2 127.0.0.1 >nul
copy /y "!MASTER_BLEND!" "!CHAR_BLEND!" >nul
if errorlevel 1 (echo  WARNING: character.blend copy failed, retrying... & ping -n 3 127.0.0.1 >nul & copy /y "!MASTER_BLEND!" "!CHAR_BLEND!" >nul)
echo  GLB updated: !OUTPUT_GLB!

echo.
echo  Done - model ^(!MODEL_KEY!^) updated
echo.
echo  Add another animation or press Enter to finish.
echo.
goto ANIM_LOOP

:FINISH
del "%TEMP%\character_bvh*.blend" >nul 2>&1
del "%TEMP%\character_bvh*.blend1" >nul 2>&1
del "%TEMP%\*.fbx" >nul 2>&1

echo.
echo ============================================================
echo  PIPELINE COMPLETE
echo ============================================================
echo.
echo  Model: !MODEL_KEY!
echo  Blend: !CHAR_BLEND!
echo  GLB:   !OUTPUT_GLB!
echo.
dir "%OUTPUT%" /b 2>nul
echo.
pause
exit /b 0
