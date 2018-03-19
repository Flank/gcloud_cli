@echo off
setlocal enabledelayedexpansion
set /P input=
echo(!input!
echo test output
echo test error>&2
%COMSPEC% /C exit 1
