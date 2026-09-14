REM SPDX-License-Identifier: Apache-2.0
@echo off
setlocal
cd /d "%~dp0\..\.."
call conda activate nisar-training
if errorlevel 1 (
 echo ERROR: Could not activate nisar-training.
 pause
 exit /b 1
)
echo === Environment ===
conda env list
echo.
echo === Python ===
python --version
where python
echo.
echo === Core packages ===
python -c "import numpy,scipy,pandas,matplotlib,h5py,xarray,rasterio,geopandas,psutil,pyproj,nisar_utils; print('ALL CORE IMPORTS: PASS')"
echo.
pause
