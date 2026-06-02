# 游戏语音实时翻译器 - README

## 🎮 功能特性
- **实时音频捕获**: 使用 WASAPI Loopback 捕获系统音频输出（不是麦克风）
- **本地语音识别**: 基于 faster-whisper 的离线英文转文字
- **智能翻译**: 硅基流动 API 的英文→中文翻译，针对游戏术语优化
- **游戏浮窗**: 透明置顶窗口，在游戏内显示翻译结果
- **手机端同步**: WebSocket 实时推送到手机浏览器
- **全局热键**: Ctrl+Shift+T/C/P 快速控制

## 📁 项目结构
```
game_voice_translator/
├── main.py              # 主程序
├── audio_capture.py     # 音频捕获模块
├── speech_recognition.py # Whisper 语音识别
├── translator.py        # 硅基流动 API 翻译
├── overlay.py           # PyQt5 游戏浮窗
├── mobile_server.py     # 手机端 WebSocket 服务器
├── config.example.json  # 配置模板
├── config.json          # 本地配置文件（不会提交到 Git）
├── requirements.txt     # Python 依赖
├── install.bat          # 安装脚本
├── run.bat              # 启动脚本
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖
双击 `install.bat` 或手动运行：
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
首次使用先复制配置模板：
```bash
copy config.example.json config.json
```

然后编辑 `config.json`，填入你的硅基流动 API Key：
```json
"translation": {
    "api_key": "你的硅基流动 API Key",
    "model": "Qwen/Qwen3.5-4B"
}
```

硅基流动提供免费可用的模型/额度，例如模板里默认使用的 `Qwen/Qwen3.5-4B`。只需要注册账号并创建一个 API Key 即可调用；具体免费模型和额度以官网为准。

注册/获取 API Key：<https://cloud.siliconflow.cn/i/iA6DF2nP>

### 3. 设置音频路由 (可选)
默认会优先使用 Windows WASAPI Loopback 采集当前扬声器/耳机输出，不需要选择麦克风。

如果设备列表里出现 `[系统声音] Speakers/Headphones/...` 或带有 `Loopback` 的设备，优先选择它；不要选择普通麦克风。麦克风只能录到环境声，通常录不到游戏声音。

如果只看到麦克风，可以运行 `install.bat` 更新依赖，或手动安装：
```bash
pip install PyAudioWPatch==0.2.12.8
```

还可以安装 VB-Cable 虚拟音频设备作为备选：
1. 下载：https://vb-audio.com/Cable/
2. 安装后，将系统默认音频输出切换到 VB-Cable
3. 游戏音频将通过 VB-Cable 被捕获

### 4. 启动程序
双击 `run.bat` 或运行：
```bash
python main.py
```

## 🎯 使用说明

### 浮窗控制
- **Ctrl+Shift+T**: 切换浮窗显示/隐藏
- **Ctrl+Alt+C**: 清空翻译历史
- **Ctrl+Alt+S**: 暂停/恢复翻译
- **拖拽浮窗**: 可移动位置

### 手机端访问
1. 确保电脑和手机在同一局域网
2. 手机浏览器访问：`http://电脑IP:8765/mobile`
3. 实时接收翻译结果

### 配置调优
编辑 `config.json`：

| 配置项 | 说明 |
|--------|------|
| `whisper.model_size` | 模型大小: tiny/base/small/medium (越大越准越慢) |
| `overlay.position` | 浮窗位置: top/bottom/left/right |
| `overlay.text_color` | 文字颜色 (十六进制) |
| `audio.sample_rate` | 采样率 (推荐 16000) |
| `translation.temperature` | 翻译创造性 (0.1~1.0) |

## 🔧 故障排除

### 1. 无法捕获音频
- 优先选择 `[系统声音]` / `Loopback` 设备，不要选普通麦克风
- 运行 `python list_devices.py`，确认能看到系统声音设备
- 确保游戏声音正在从你选择的扬声器/耳机播放
- 如果只看到麦克风，重新运行 `install.bat` 安装 PyAudioWPatch
- 如果使用 VB-Cable，确保系统音频输出已切换到 VB-Cable
- 尝试以管理员身份运行

### 2. 语音识别不准确
- 调高 `whisper.model_size` (small → medium)
- 降低游戏内背景音乐音量
- 确保麦克风/音频质量良好

### 3. 翻译延迟高
- 检查网络连接
- 降低 `whisper.model_size` 以加快识别
- 使用本地翻译模型 (需自行部署)

### 4. 手机端无法连接
- 检查防火墙是否放行 8765 端口
- 确认手机和电脑在同一局域网
- 尝试使用电脑 IP 而非 localhost

## 📊 性能指标

| 组件 | 延迟 | 资源占用 |
|------|------|----------|
| 音频捕获 | < 50ms | 低 |
| Whisper-small | 1-2s | CPU: 中等 / GPU: 低 |
| 硅基流动 API | 0.5-1.5s | 网络依赖 |
| 浮窗渲染 | < 10ms | 低 |

## 🎮 游戏兼容性
- ✅ **FPS 游戏**: CS2, Valorant, Apex, PUBG
- ✅ **MOBA**: League of Legends, Dota 2
- ✅ **合作游戏**: Among Us, Phasmophobia
- ✅ **MMO**: World of Warcraft, Final Fantasy XIV
- ⚠️ **DRM 保护**: 某些游戏可能阻止音频捕获

## 📝 注意事项
1. 首次运行会下载 Whisper 模型（默认 base 约 150MB；更大模型会占用更多空间）
2. 需要稳定的网络连接用于翻译 API
3. 建议在游戏前启动本程序
4. 手机端需要保持浏览器页面打开

## 🤝 贡献
欢迎提交 Issue 和 Pull Request 改进项目！

## 📄 许可证
MIT License
