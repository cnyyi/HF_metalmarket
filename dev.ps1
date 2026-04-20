<#
 # 一键启动开发服务器
 # 1. 自动杀掉占用 5000 端口的旧进程
 # 2. 启动 Flask 开发服务器
 #>
param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Continue"

# 查找并杀掉占用端口的进程
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($connections) {
    $procIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $procIds) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Write-Host "杀掉旧进程: PID=$procId ($($proc.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $procId -Force
        } catch {
            Write-Host "进程 $procId 已不存在" -ForegroundColor DarkGray
        }
    }
    Start-Sleep -Milliseconds 500

    # 二次确认
    $check = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($check) {
        Write-Host "端口 $Port 仍被占用，等 2 秒再试..." -ForegroundColor Red
        Start-Sleep -Seconds 2
        $check2 = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($check2) {
            Write-Host "端口 $Port 无法释放，请手动处理" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "端口 $Port 已释放" -ForegroundColor Green
} else {
    Write-Host "端口 $Port 空闲" -ForegroundColor Green
}

# 启动正式开发入口 app.py
Write-Host "`n启动开发服务器 (正式入口: app.py, 端口 $Port)..." -ForegroundColor Cyan
python app.py
