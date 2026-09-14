REM SPDX-License-Identifier: Apache-2.0
@echo off
setlocal
title NISAR GCOV Training - Start

where conda >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda was not found.
    echo Open this file from a Miniconda Prompt, or install Miniconda first.
    pause
    exit /b 1
)

cd /d "%~dp0\..\.."
call conda activate nisar-training
if errorlevel 1 (
    echo ERROR: Could not activate nisar-training.
    echo Run INSTALL_NISAR_TRAINING.bat first.
    pause
    exit /b 1
)

echo ================================================================
echo NISAR GCOV TRAINING
echo ================================================================
echo Environment: nisar-training
echo Starting JupyterLab from the repository root...
echo ================================================================
python -m jupyter lab
