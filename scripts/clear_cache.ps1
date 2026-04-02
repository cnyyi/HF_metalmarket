# 彻底清除缓存并重启应用程序

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "清除所有 Python 缓存" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 删除所有 __pycache__ 目录
Write-Host "`n1. 删除所有 __pycache__ 目录..." -ForegroundColor Yellow
$pypyCacheDirs = Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue
$count = 0
foreach ($dir in $pypyCacheDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $count++
}
Write-Host "   删除了 $count 个 __pycache__ 目录" -ForegroundColor Green

# 删除所有 .pyc 文件
Write-Host "`n2. 删除所有 .pyc 文件..." -ForegroundColor Yellow
$pycFiles = Get-ChildItem -Path . -File -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
$count = 0
foreach ($file in $pycFiles) {
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    $count++
}
Write-Host "   删除了 $count 个 .pyc 文件" -ForegroundColor Green

# 删除所有 .pyo 文件
Write-Host "`n3. 删除所有 .pyo 文件..." -ForegroundColor Yellow
$pyoFiles = Get-ChildItem -Path . -File -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue
$count = 0
foreach ($file in $pyoFiles) {
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    $count++
}
Write-Host "   删除了 $count 个 .pyo 文件" -ForegroundColor Green

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "缓存清除完成！" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n现在可以运行: python app.py" -ForegroundColor Yellow