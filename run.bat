@echo off
chcp 65001 >nul
echo ============================================
echo   VoxGo - 启动
echo ============================================
echo.

:: 检查依赖
if not exist "requirements.txt" (
    echo [错误] 请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

:: 检查配置文件
if not exist "config.json" (
    if exist "config.example.json" (
        copy /Y "config.example.json" "config.json" >nul
        echo [提示] 已从 config.example.json 生成 config.json
        echo [提示] 请在 config.json 或设置界面中填入你的 OpenAI 兼容 API Key
        echo        注册/获取: https://cloud.siliconflow.cn/i/iA6DF2nP
        echo.
        pause
    ) else (
        echo [错误] config.json 不存在，且未找到 config.example.json
        pause
        exit /b 1
    )
)

:: 检查 API Key 配置
set NEED_API_KEY=0
findstr /C:"YOUR_OPENAI_COMPATIBLE_API_KEY" config.json >nul
if %errorlevel% equ 0 set NEED_API_KEY=1
findstr /C:"YOUR_SILICONFLOW_API_KEY" config.json >nul
if %errorlevel% equ 0 set NEED_API_KEY=1
if "%NEED_API_KEY%"=="1" (
    echo [警告] 请在 config.json 或设置界面中填入你的 OpenAI 兼容 API Key
    echo 默认使用硅基流动兼容接口，硅基流动提供免费可用的模型/额度，注册并创建 API Key 即可调用
    echo 获取地址: https://cloud.siliconflow.cn/i/iA6DF2nP
    echo.
    echo 是否继续？(Y/N)
    set /p choice=
    if /i not "%choice%"=="Y" exit /b 1
)

:: 启动程序
echo 正在启动 VoxGo...
echo 按 Ctrl+C 停止程序
echo.

python main.py

echo.
echo ============================================
echo   程序已停止
echo ============================================
pause
