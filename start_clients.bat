@echo off
chcp 936 >nul
setlocal enabledelayedexpansion


set setup_node_ip=127.0.0.1
set alg=1

set client_count=10
set vectorsize=100000
::  python setup.py 100
::  python aggregator.py 1234 127.0.0.1

set CONDA_PATH=C:\ProgramData\anaconda3
call %CONDA_PATH%\Scripts\activate.bat tenseal


for /L %%i in (1,1,%client_count%) do (
    echo start client %%i...
    start /B python client.py %alg% %vectorsize% %client_count% %setup_node_ip% %%i
)

echo all client started
endlocal
