@echo off
for %%i in (*.jpg) do E:\Sudao-Project\Landmark-Annotation\dji_thermal_sdk_v1.4_20220929\utility\bin\windows\release_x64\dji_irp.exe -s %%i -a measure -o %%~ni.raw --measurefmt float32 --humidity 50.0 --emissivity 0.95 --reflection 25.0 --distance 5.0
pause