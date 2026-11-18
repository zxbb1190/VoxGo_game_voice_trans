# VoxGo 0.6.1 发布验收

[GitHub Release](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/tag/v0.6.1) 于 2026-11-18T02:23:25Z 发布。[Windows 正式构建](https://github.com/zxbb1190/VoxGo_game_voice_trans/actions/runs/44221733203) 使用标签提交 `89b70b98`。官网与软件更新窗口共用五条面向用户的中英文更新说明，详细 Lite 升级步骤见[官网更新日志](https://voxgo.cn/changelog/v0.6.1/)。

| GitHub 附件 | 字节数 | 实际下载 SHA256 |
|---|---:|---|
| [lite](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v0.6.1/VoxGo-v0.6.1-lite.zip) | 138,908,727 | `449a975720e2d675287259074a69832f534a8d2237068ee297f02beaead81541` |
| [full](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v0.6.1/VoxGo-v0.6.1-full.zip) | 718,707,685 | `23cbfe6cc48078dbd9b8ccc8bead15c86cda94f245314638344a0fed60f93fba` |
| [full-cuda](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v0.6.1/VoxGo-v0.6.1-full-cuda.zip) | 1,309,425,103 | `2c4f75d82425dd81794993000f3de6f1518953bffab5b198eccd5c8f9f4474ec` |
| [cuda-runtime](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v0.6.1/VoxGo-v0.6.1-cuda-runtime.zip) | 590,591,593 | `bce73acaf7dc76c6a140dac955def51a2ab86ab4bcbdb645d7463a4cbc123a0d` |

- 正式构建和 GitHub Release 创建步骤成功。Actions 向 GitCode 传输 15 分钟后，国内固定地址仍返回 HTTP 404。GitHub 更新清单先于镜像生效。本次停止仍在进行的云端上传，按仓库的本机补发流程同步同一份 Lite，完整回读后再登记国内更新源。
- GitHub 四个正式 ZIP 完整下载，逐包校验 SHA256、ZIP CRC 和内容。[GitCode 国内 Lite](https://gitcode.com/zxbb1190/VoxGo/releases/download/v0.6.1/VoxGo-v0.6.1-lite.zip) 从公开固定地址完整下载，字节数与 SHA256 均与 GitHub Lite 一致。[在线更新清单](https://voxgo.cn/update.json) 的四个正式地址、SHA256、国内版本和摘要均已回读。
- Lite、Full 和 Full-CUDA 通过真实更新器解包，在 Windows 上实际运行各自的 `VoxGo.exe --help`。各包的安装标记和默认配置正确，95 个冻结项目模块（含入口）与本次源码一致。Lite 无内置 Whisper 权重，两个 Full 包均包含 base 和 small。在本机 CPU 上用正式 Full 包的两个模型分别识别了同一段英文录音。
- 本机 Windows 运行 881 项回归，全部通过，包括两项私有 Worker 契约。综合语句与分支覆盖率为 77.93%。[日常 CI](https://github.com/zxbb1190/VoxGo_game_voice_trans/actions/runs/44222998616) 通过。CI 的两项私有契约由本机补足。
- [官网字幕对比](https://voxgo.cn/#cinema) 在中、英、日、韩、俄五个首页共使用 10 张 Windows 原生窗口截图，取自同一句对白的实际翻译结果。线上逐图回读与源图一致。真实 Chrome 在 1440、390、320 像素宽度共检查 15 个视图，截图解码、章节跳转与页面宽度检查均通过。中英文 README 及图片链接已回读。
- 使用 0.6.0 的原生 Qt 更新窗口读取正式清单，中英文各显示五条短说明。详细升级步骤和 SHA256 留在下载页。
- 本机为 AMD 显卡，未进行 NVIDIA GPU 推理。应用包启动验证使用帮助入口。实际游戏内的全屏交互和语音翻译准确度不属于此次发包复验。之前 Windows 原生自动操作未确认电影模式语言菜单在移出时能持续打开，切换到 Beta 语言也可能显示提示。
