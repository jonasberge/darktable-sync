@echo off
SETLOCAL

set BASE_DIR=F:\Darktable
set INSTALL_DIR=%BASE_DIR%\install
set PREFIX=%INSTALL_DIR%\darktable-windows
set DARKTABLE_BIN_DIR=%PREFIX%\bin
set MERGE_SCRIPT=%INSTALL_DIR%\scripts\merge-config.py
set WINDOWS_CONFIG_DIR=%BASE_DIR%\config-windows
set LINUX_CONFIG_DIR=%BASE_DIR%\config-ubuntu

rem for %%F in (%DARKTABLE_BIN%) do set DARKTABLE_BIN_DIR=%%~dpF

echo (merging config directories)
cd "%BASE_DIR%"
call :exec python "%MERGE_SCRIPT%" -t 2 -m newest -d windows -l "%LINUX_CONFIG_DIR%" -w "%WINDOWS_CONFIG_DIR%" --debug

rem source: https://stackoverflow.com/a/26732879
for /f "tokens=1,* delims= " %%a in ("%*") do set ALL_BUT_FIRST=%%b

echo (launching darktable) %ALL_BUT_FIRST%
cd "%DARKTABLE_BIN_DIR%"
call :exec "%DARKTABLE_BIN_DIR%\%1.exe" "--configdir" "%WINDOWS_CONFIG_DIR%" %ALL_BUT_FIRST%

goto :eof

:exec
echo %*
%*
goto :eof
