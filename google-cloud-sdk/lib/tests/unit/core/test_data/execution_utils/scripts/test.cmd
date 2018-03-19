@echo off
chcp 1252>NUL
set /P input=
echo input: %input%
echo argument: %1
echo test output
(
  echo test error
) 1>&2
%COMSPEC% /C exit 1
