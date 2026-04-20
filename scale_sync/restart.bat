@echo off
chcp 65001 >nul 2>&1
title 宏发过磅同步服务 - 重启

echo ============================================
echo   宏发过磅同步服务 - 停止旧进程并重启
echo ============================================
echo.

:: ---- 1. 停止 nssm 服务（如果存在） ----
where nssm >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [1/4] 检测到 nssm，停止服务...
    nssm stop HF_ScaleSync >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo       nssm 服务已停止
) else (
    echo [1/4] 未检测到 nssm，跳过
)

:: ---- 2. 停止计划任务（如果存在） ----
schtasks /query /tn "HF_ScaleSync" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [2/4] 检测到计划任务，停止并删除...
    schtasks /delete /tn "HF_ScaleSync" /f >nul 2>&1
    echo       计划任务已删除
) else (
    echo [2/4] 未检测到计划任务，跳过
)

:: ---- 3. 杀掉残留的 python 进程（运行 scale_sync.py 的） ----
echo [3/4] 检查残留进程...
for /f "tokens=2" %%p in (
    'wmic process where "commandline like '%%scale_sync.py%%' and name='python.exe'" get processid /format:list 2^>nul ^| find "ProcessId="'
) do (
    echo       杀掉进程 PID=%%p
    taskkill /pid %%p /f >nul 2>&1
)
timeout /t 1 /nobreak >nul
echo       残留进程已清理

:: ---- 4. 启动新服务 ----
echo [4/4] 启动新服务...
cd /d "%~dp0"

where nssm >nul 2>&1
if %ERRORLEVEL%==0 (
    nssm install HF_ScaleSync "python" "%~dp0scale_sync.py" >nul 2>&1
    nssm set HF_ScaleSync AppDirectory "%~dp0" >nul 2>&1
    nssm set HF_ScaleSync Description "宏发金属交易市场-过磅数据同步服务" >nul 2>&1
    nssm set HF_ScaleSync Start SERVICE_AUTO_START >nul 2>&1
    nssm start HF_ScaleSync >nul 2>&1
    if %ERRORLEVEL%==0 (
        echo       nssm 服务已启动
    ) else (
        echo       nssm 启动失败，回退到直接运行
        start "" /b python scale_sync.py
        echo       python 进程已后台启动
    )
) else (
    start "" /b python scale_sync.py
    echo       python 进程已后台启动
)

echo.
echo ============================================
echo   重启完成！
echo ============================================
echo.
echo 查看日志: type logs\scale_sync.log
echo 手动停止: taskkill /f /im python.exe /fi "commandline like scale_sync.py"
echo.
pause
