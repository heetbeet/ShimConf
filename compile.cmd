@echo off
setlocal EnableDelayedExpansion

REM Detecting Visual Studio
for /l %%i in (2040, -1, 2019) do (
    if exist "C:\Program Files\Microsoft Visual Studio\%%i\Community\VC\Auxiliary\Build\vcvars64.bat" (
        call "C:\Program Files\Microsoft Visual Studio\%%i\Community\VC\Auxiliary\Build\vcvars64.bat"
        goto :found_vcvarsall
    )
)
echo Error: Visual Studio not found. Install Visual Studio with C++ support and try again.
exit /b 1

:found_vcvarsall

REM Go to the project directory
cd /d "%~dp0."

REM Compile all the C++ files
mkdir build 2> NUL
for %%f in (*.cpp) do (
    cl /c /Fobuild/ /EHsc /std:c++20 /W3 %%f
)

REM Link all the object files to the executable
mkdir dist 2> NUL
link /out:dist\main.exe build\*.obj kernel32.lib

endlocal

if /i "%comspec% /c %~0 " equ "%cmdcmdline:"=%" pause
