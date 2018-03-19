@echo off
REM /bin/sh translations inline
REM First line means "set +x" (which is default in sh)

REM "echo out"
echo out

REM "echo app.yaml contents > $3/app.yaml"
echo app.yaml contents> %3\app.yaml

REM "echo service-yaml path$1 1>&2"
1>&2 echo service-yaml path: %1

REM "echo app-dir path$2 1>&2"
1>&2 echo app-dir path: %2

REM "exit 0"
%COMSPEC% /C exit 0
