# 首次字幕、指定应用收音与社区邀请：本地验收

状态：开发完成、源代码验收通过；未提交、未推送、未打包或发布。保留了工作区已有的清理和输出保护改动。

## 用户能看到的变化

1. 完成首次设置后打开“字幕检查”，用正式链路检查模型、声音、识别、翻译和可见浮窗。设置中的接口测试不能使这项检查通过。检查显示当前音源和音量，失败时提供设置、模型重试、恢复翻译与重新检查入口；最后由用户确认游戏上方确实可见。关闭或跳过检查不会记作成功，关闭向导也不再自动完成设置。
2. 设置和首次向导都可选择“只翻译指定应用”。选择运行中的应用窗口，Windows 捕获该进程及子进程的音频；浮窗持续标明当前音源。目标退出、进程身份变化、目标不明确或系统不支持时暂停收音，不回退到系统声音。重启只保存可执行文件路径，不保存失效 PID；多个同路径实例需要重新选择。
3. 有效译文进入可见浮窗后，显示一次社区邀请，提供交流游戏设置、排查问题和参加新版本测试的入口。不会自动打开浏览器。紧凑或锁定状态延后显示；关闭后持久化，不重复出现。首次成功时间、检查确认、邀请已显示标记只存于本机，本次未增加服务端遥测事件。

切换音源同时失效化旧识别/翻译结果、清理上下文并重新校准音量门限。设置窗口的旧配置副本不会覆盖新产生的首次成功状态。按 Esc 退出向导或设置也会停止音量测试、取消接口测试。

## 验证

- 新增 33 项回归（含发布默认值保护），全量 794 项测试通过，无跳过。包含两个私有 Worker 契约测试；没有访问生产接口。
- 语句/分支综合覆盖率 75.57%，高于 74% 门槛；Ruff、源码编译、历史证据索引和 `git diff --check` 均通过。
- Windows 原生隔离：目标父进程不发声，由子进程播放 440 Hz；独立应用同时播放 880 Hz。真实声卡输出与进程回环捕获通过，目标/非目标频率幅度比约 112.29 dB。目标退出、失效进程身份拒绝通过。该数字只是此合成音实验的频谱结果，不是所有应用的隔离性能保证。
- 真实游戏录音播放 → 原生应用收音 → 本地 Whisper → 本地 OPUS → Qt 浮窗 → 两个手机 WebSocket：121 秒运行输出 13 条有效字幕，桌面与两个手机连接各 13 条，错误计数为 0，检查五步全部通过。
- 更新后的原生界面复验 85.59 秒：桌面和两个手机连接各 10 条，错误计数为 0；再次确认目标退出后暂停、邀请不重复和正常关闭。
- 独立延迟采样复验 86.23 秒：9 条有效字幕，桌面和两个手机连接各 9 条；按字幕 ID 记录 9 个完整处理耗时，P50 为 1659 ms、P95 为 1955.2 ms。这里的起点是**音频切片产生**，终点是浮窗更新回调，**不包含等待切片的时间，也不是声音结束到屏幕像素呈现的完整延迟**。样本量小，不作版本性能比较。
- 9 组真实模型音频回归全部通过：异常输出被拦截，正常语音、低音量语音和短口令保留；短口令样本包含明确标记的 SAPI 合成语音。
- 原生验收使用隔离配置、缓存模型和回环 HTTP/WS，阻止外部网络；用户原配置文件哈希保持一致。核心服务正常关闭。残留的一个后台线程确认是 `tqdm` 的 daemon 监视线程，没有音频捕获、ASR 或翻译任务残留。

自动测试还覆盖：旧音频/旧语言版本不能完成新检查，失败/空译文/删除字幕行不能触发成功，隐藏浮窗需显示后才确认，邀请关闭与配置持久化，源切换失效化、停止、重试，以及五种界面语言的文案。

## 入口与运行方法

- 功能代码：`voxgo/ui/live_check.py`、`voxgo/runtime/first_success.py`、`voxgo/ui/audio_source.py`、`voxgo/audio/process_loopback.py`。
- 回归：`tests/test_first_success.py`、`tests/test_process_audio.py`、`tests/test_release_speech_policy.py`。
- 每日 CI：`.github/workflows/quality.yml` 增加 UTC 20:00（北京时间次日 04:00）调度，保留 push/PR/manual 触发。推送至默认分支后才会实际生效；本次没有远端 CI 结果。

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv-win\Scripts\python.exe -m unittest tests.test_first_success tests.test_process_audio -v
.\.venv-win\Scripts\python.exe scripts/check_process_audio.py --output diagnostics/process-audio.json
.\.venv-win\Scripts\python.exe scripts/check_output_guard_audio.py --output diagnostics/output-guard.json
```

第二条命令会通过真实声卡播放轻声测试音，需 Windows build 20348+ 和可用播放设备。硬件验收不放入普通托管 CI，避免无声卡环境被误记成通过。

本机原始证据位于 `diagnostics/asr-benchmark/first-success-20261111/`（git 忽略）：`process-audio-final.json`、`output-guard.json`、`native-flow/actual-flow.json`、`native-final/actual-flow.json`、`native-latency/actual-flow.json`，以及原生 Qt 截图。验收脚本与测试/覆盖率结果一起保留在该目录的 `tools/`、`quality/` 下。

## 尚未覆盖的发布验收

没有执行收费 API 请求，没有验证所有游戏/反作弊/受保护音频、独占全屏、所有声卡、Windows 旧版本或安装包升级。仍需真游戏人工确认，不能用本地回归数字代替这些结论。本次也没有改变 Pro、付费、许可证或遥测授权策略。

实现依据：[Microsoft process loopback API](https://learn.microsoft.com/en-us/windows/win32/api/audioclientactivationparams/ne-audioclientactivationparams-process_loopback_mode)、[官方应用回环示例](https://learn.microsoft.com/en-us/samples/microsoft/windows-classic-samples/applicationloopbackaudio-sample/)。
