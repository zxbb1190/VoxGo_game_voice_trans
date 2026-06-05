@echo off
chcp 65001 >nul
echo ============================================
echo   VoxGo - 环境安装
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 升级 pip...
python -m pip install --upgrade pip -q

echo [2/3] 安装依赖包（含 PyAudioWPatch，用于捕获系统声音）...
python -m pip install -r requirements.txt -q

echo [3/3] 安装 VB-Cable 虚拟音频设备 (可选，用于捕获系统音频)...
echo.
echo 请手动下载安装 VB-Cable:
echo https://vb-audio.com/Cable/
echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo 使用前请:
echo   1. 编辑 config.json，填入你的硅基流动 API Key
echo   2. 音频设备优先选择 [系统声音] / Loopback，不要选普通麦克风
echo   3. 运行 run.bat 启动 VoxGo
echo.
pause
