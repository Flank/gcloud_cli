@echo off
REM /bin/sh translations inline
REM First line means "set +x" (which is default in sh)

REM "echo out"
echo out

REM "echo 'service-yaml path: $1' 1>&2"
1>&2 echo service-yaml path: %1

REM "echo app-dir path$2 1>&2"
1>&2 echo app-dir path: %2

REM "exit 1"
%COMSPEC% /C exit 1
