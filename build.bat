@echo off
chcp 65001 >nul
echo ===================================
echo    SteaMiss 打包脚本
echo ===================================
echo.

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    echo 激活虚拟环境 .venv...
    call .venv\Scripts\activate.bat
    echo.
) else (
    echo 警告: 未找到虚拟环境 .venv
    echo.
)

REM 清理旧的构建文件
echo [1/4] 清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo 完成!
echo.

REM 使用 PyInstaller 打包
echo [2/4] 开始打包...
pyinstaller --clean --noconfirm SteaMiss.spec
if errorlevel 1 (
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)
echo 完成!
echo.

REM 复制配置文件与可覆盖的资源到 dist 目录
echo [3/4] 复制必要文件...
if not exist dist\config mkdir dist\config
echo 完成!
echo.

echo [4/4] 打包完成!
echo.
echo 生成的 exe 文件位于: dist\SteaMiss.exe
echo.
pause
