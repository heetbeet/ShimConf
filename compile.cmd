@echo off
setlocal EnableDelayedExpansion

REM Find python3, then run scripts/compile.py

set python3=
REM python.exe -V
for /f "delims=" %%A in ('where python.exe') do (
    for /f "delims=" %%B in ('"%%A" -V 2^>^&1') do (
        if "%%B" gtr "Python 3" (
            set "python3=%%A"
            goto :python3_found
        )
    )
)

REM python3.exe -V
if not defined python3 (
    for /f "delims=" %%A in ('where python.exe') do (
        for /f "delims=" %%B in ('"%%A" -V 2^>^&1') do (
            if "%%B" gtr "Python 3" (
                set "python3=%%A"
                goto :python3_found
            )
        )
    )
)

REM "%USERPROFILE%\Anaconda3\python.exe" 
if not defined python3 (
    if exist "%USERPROFILE%\Anaconda3\python.exe" (
        set "python3=%USERPROFILE%\Anaconda3\python.exe"
        goto :python3_found
    )
)

echo Error, no python 3 found, please install https://www.anaconda.com/download/
exit /b -1

:python3_found

call "%python3%" "%~dp0\scripts\compile.py" %*

if /i "%comspec% /c %~0 " equ "%cmdcmdline:"=%" pause
