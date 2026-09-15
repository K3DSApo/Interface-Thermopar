@echo off
setlocal
set "ROOT=%~dp0.."
pushd "%ROOT%"
py -3 -m app.main --port 8765 --data-dir "%ROOT%\sesiones"
popd
endlocal
