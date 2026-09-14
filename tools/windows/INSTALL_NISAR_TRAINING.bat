REM SPDX-License-Identifier: Apache-2.0
@echo off
setlocal EnableExtensions EnableDelayedExpansion
title NISAR GCOV Training - One-Time Setup

echo ================================================================
echo NISAR GCOV TRAINING - ONE-TIME PARTICIPANT SETUP
echo ================================================================
echo.
echo This script assumes Miniconda is already installed.
echo It will create/use the Conda environment: nisar-training
echo and register the Jupyter kernel: NISAR Training.
echo.

where conda >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda was not found in this command window.
    echo.
    echo Please:
    echo   1. Install Miniconda for Windows.
    echo   2. Open "Miniconda Prompt" from the Windows Start menu.
    echo   3. Run this installer again from the repository folder.
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0\..\.."

echo [1/5] Checking package...
if not exist "environment.yml" (
    echo ERROR: environment.yml was not found.
    echo Run this script from the root of the complete training package.
    pause
    exit /b 1
)
if not exist "nisar_utils" (
    echo ERROR: nisar_utils folder was not found.
    echo Please use the COMPLETE training package.
    pause
    exit /b 1
)
for %%F in ("01_Setup_and_Product_Selection.ipynb" "02_Session_Check_and_Product_Orientation.ipynb" "03_NISAR_L1_Product_Explorer_Metadata_First.ipynb" "04_NISAR_L2_GCOV_Product_Explorer.ipynb" "05_Large_NISAR_Data_Performance_and_Windowed_Access.ipynb" "06_L2_GCOV_Spatial_Subsetting_AOI_LATLON_DEFAULT.ipynb" "07_L2_GCOV_Quality_Control_Statistics_and_Masks.ipynb" "08_L2_GCOV_Visualization_RGB_GCS.ipynb" "09_Advanced_L2_GCOV_Frequency_Masks_Metadata_and_Batch_Processing.ipynb" "10_L2_GCOV_GeoTIFF_Export_and_QGIS_Validation.ipynb" "11_End_to_End_NISAR_L2_GCOV_Capstone.ipynb" "12_Trainer_Troubleshooting_Performance_and_Session_Management.ipynb") do (
    if not exist "%%~F" (
        echo ERROR: Required training notebook missing: %%~F
        echo The complete repository must be extracted intact.
        pause
        exit /b 1
    )
)
if exist "notebooks" (
    echo ERROR: Stale notebooks folder detected. Use the repository root structure.
    pause
    exit /b 1
)

echo [2/5] Creating/checking nisar-training environment...
call conda env list | findstr /R /C:"[ ]nisar-training[ ]" >nul
if errorlevel 1 (
    echo Creating nisar-training from environment.yml...
    call conda env create -n nisar-training -f environment.yml
    if errorlevel 1 goto FAIL
) else (
    echo nisar-training already exists. No recreation needed.
)

echo [3/5] Activating nisar-training...
call conda activate nisar-training
if errorlevel 1 goto FAIL

echo [4/5] Registering Jupyter kernel...
python -m ipykernel install --user --name nisar-training --display-name "NISAR Training"
if errorlevel 1 goto FAIL

echo [5/5] Running installation checks...
python -c "import numpy, scipy, pandas, matplotlib, h5py, xarray, rasterio, geopandas, psutil, pyproj, nisar_utils; print('CORE IMPORT CHECK: PASS')"
if errorlevel 1 goto FAIL

python -c "import sys; print('Python:',sys.version.split()[0]); print('Executable:',sys.executable)"
if errorlevel 1 goto FAIL

echo.
echo ================================================================
echo SETUP COMPLETE
echo ================================================================
echo Environment : nisar-training
echo Jupyter     : NISAR Training
echo Package     : %CD%
echo.
echo NEXT STEP:
echo   Double-click START_NISAR_TRAINING.bat
echo.
echo Then open the Module 02 session check notebook before proceeding with the training sequence.
echo ================================================================
pause
exit /b 0

:FAIL
echo.
echo ================================================================
echo SETUP FAILED
echo ================================================================
echo Read the error shown above.
echo Do not create another Conda environment.
echo Contact the workshop support team if the problem remains.
echo ================================================================
pause
exit /b 1
