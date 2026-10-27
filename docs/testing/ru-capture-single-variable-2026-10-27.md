# v0.5.3 第二阶段：俄语捕获时长单变量离线验证

结论：**本轮没有可直接用于正式 RU 策略的赢家。** 仅将最大捕获从 4.5s 改为 3.0s，能够恢复铯/碘的疑似词形，但会产生被现有 Pipeline 预算规则丢弃的句尾片段。3.5s、4.0s 仍不能可靠保留碘。正式客户端、默认配置、过滤阈值、翻译、Telemetry 均未修改。

## 1. 修改与执行范围

- 工作树：`C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator`，分支 `codex/multilingual-online-053`，开始 HEAD `a67a656386c8e3647b0ef7e2d5372f250c22c16c`，开始时干净。未切换或清理其他工作树。
- `voxgo/` 相对开始 HEAD 和 `645c6ace` 的 diff 均为空。实验执行的是 a67a6563 加本次工具补丁，补丁文件的精确 SHA256、依赖版本、模型文件 SHA256 保存在每个 `result.json` 和 `plan.json`，而非把未提交工具冒称已有 Git 版本。
- 仅新增两份工具、一份 15 项测试、本报告及新证据；已有四份评测脚本和 10 月 27 日 paired 原始结果未改。
- 无在线 Provider 实例、无翻译请求、无 Analytics 实例；离线守卫拒绝 DNS/连接/绑定/发送及 Analytics 导入。16 个子进程的网络/Analytics 导入尝试数均为 0。模型只读使用既有缓存，无下载。
- 本轮客户端全量测试的 Analytics 测试使用其原有临时目录/受控夹具；实验运行器本身不初始化 Analytics。没有生产请求或生产操作。

| 新增文件 | 函数/类 | 作用与边界 |
|---|---|---|
| `scripts/offline_russian_capture_ab.py` | `load_pcm`、`local_base`、`make_config`、`schedule`、`run_child`、`per_clip`、`summarize` | 校验源 WAV/模型，独立 RAM 配置，正反顺序独立进程，真实 Capture→Pipeline→Whisper→过滤→翻译入口语言门，停在翻译边界；CLI 不加载用户设置。 |
| `scripts/offline_asr_observer.py` | `ObservedCapture`、`ObservedPipeline`、`ObservedRecognizer`、`observe_merge` | 委托正式方法执行决策；跟踪实际队列对象的帧来源、积压块拼接、前卷、合并父子关系、丢弃、raw/保留/翻译输入、实际归一化数组和资源。仅评测进程内包装，不写入正式链路。 |
| `tests/test_offline_russian_capture_ab.py` | 15 项测试 | 覆盖配置不变与快照、单变量、校验、禁覆盖、缺模型、断网、相同静音的帧定位、原始队列溢出、实际前卷、合并来源、原过滤和线程停止。 |

正式决策仍来自 `SystemAudioCapture.process_audio`（`voxgo/audio/capture.py:999`）、`SpeechPipeline.on_speech_detected/_process`（`voxgo/asr/pipeline.py:513/629`）、`SpeechRecognizer.transcribe_audio_bytes_with_language`（`voxgo/asr/whisper_engine.py:949`）及 `should_skip_translation_for_language`（`voxgo/translation/base.py:218`）。代码位置对应 a67a6563，运行时与 645c6ace 一致。工具没有重写切段/过滤算法；语言门采用 app 同样的原函数，并保留 remember_transcript 行为。

## 2. 实际生效参数与实验设计

主机：i7-13700，16 核/24 逻辑处理器。无游戏、真实 GUI、物理 loopback 或低配真机。

| 项目 | 全矩阵实际值 |
|---|---|
| 实际模型 | 多语言 base，Systran faster-whisper-base `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66` |
| 模型文件 | `model.bin` 145217532 bytes；SHA256 和其他模型文件见 plan.json。`.models` 是指向既有 E 盘模型缓存的 junction，仅使用本地已核验文件。 |
| 设备/计算/线程/worker | CPU / INT8 / 2 / 1；全部真实推理记录均为 CPU INT8 |
| beam / language / temperature / previous text | 1 / auto→None / 0.0 / False |
| Prompt | none / 空；不修改原 Prompt |
| 过滤 | 原有全部 Pipeline 过滤及翻译入口语言门，最低语言概率 0.35 不变 |
| VAD | 捕获器 WebRTC VAD；Whisper vad_filter=False。Whisper 中未启用的 max_speech_duration_s 始终保持 4.5，以免引入第二个解码变量。 |
| 音频 | 原始单声道 PCM16 16kHz；120ms 输入块，先 3s 静音，铯/碘录音，2s 静音，蚊子录音，2s 静音，再 1s 静音；最后不足块按 paired 原方式补零。 |
| 前卷 / idle | 450ms / 450ms；实际起音前卷均为 5760 帧=360ms，不能把名义 450ms 当作精确裁切。 |
| 其余配置 | 原 language_aware RU 的 Fast/low 调度：pending 0.30s、弱候选 cooldown 0.35s；逐字段见 actual config。 |

| 组 | max_speech_seconds | pre_roll_ms | idle_ms | 请求处理节拍 |
|---|---:|---:|---:|---|
| A | 4.5 | 450 | 450 | 5ms、100ms |
| B | 3.0 | 450 | 450 | 5ms、100ms |
| C | 3.5 | 450 | 450 | 5ms、100ms |
| D | 4.0 | 450 | 450 | 5ms、100ms |

每组在每个节拍下正反顺序各运行一次，共 16 个新进程、32 次流式录音回放，**只有 2 段独立且已参与调研的公开朗读录音**。每个进程先按旧 paired 工具顺序做两次整段 ASR 预热，不进入翻译。矩阵共有 64 次流式 Whisper 调用，另有 32 次整段预热；不把它们算成 96 条独立样本。所有进程采用同一源 WAV、回放流 SHA256、模型和 Whisper 配置，工作项快照与实际配置逐字段一致。

工具开发的第一次冒烟因 NumPy bool 诊断值 JSON 序列化失败而停止；保留于 `build/multilingual-online/ru-capture-tool-smoke-20261027`。修复后在全新 `ru-capture-tool-smoke2-20261027` 完整通过。以下全部数据只来自随后一次完整矩阵 `ru-max-only-20261027`，没有选择性重试实验组。

## 3. 结果：每段录音分别判断

完整逐段 raw、语言概率、过滤、翻译输入、帧区间、增益、ASR/CPU/RSS 见新证据目录 `segment-review.md` 和各运行的 `result.json`。下表对相同结果去重；两种请求节拍、正反两轮的 PCM 边界、ASR 输出、过滤与翻译输入均一致。

### 放射性铯/碘

标准原文：`Согласно ядерному управлению Японии, на заводе были обнаружены радиоактивный цезий и йод.`

流起点为 48000 帧。以下均为原 WAV 半开区间（16kHz），加 48000 即回放流位置。

| max | 第一段 WAV 帧 | 尾段 WAV 帧 | 第一段 raw | 尾段 raw；语言/概率 | 结果 |
|---|---|---|---|---|---|
| 4.5s | [3840,76800) | [76800,101760) | `Сокласно ядерному управлению Японии на заводе были обнаружены радиоактивные.` | `het seise ijoud.`；nl / 0.191841 | 尾段因 0.19<0.35 过滤，铯/碘未到翻译入口。 |
| 3.0s | [3840,51840) | [51840,101760) | `К согласной ядерному управлению Японии на заводе.` | `и полябно ружина радиоактивной цези и йод.`；ru / 0.989847 | 放射性、铯变体 `цези`、碘 `йод` 疑似保留；仍有明显拼写/句法识别错误，不能等同完整语义通过。 |
| 3.5s | [3840,61440) | [61440,101760) | `Соклассный ядерному управлению Японии, на заводе были обнаружены.` | `на радиоактивной цизи иет.`；ru / 0.986247 | 不再过滤，铯疑似命中，碘仍非可靠词形。高语言概率不能代替语义正确。 |
| 4.0s | [3840,69120) | [69120,101760) | `К согласной ядерному управлению Японии на заводе были обнаружены радио` | `активной цези иет.`；ru / 0.969846 | 输出把“放射性”拆成 `радио` / `активной`；碘仍不可靠。自动连续词匹配也会对此出现假阴性。 |

名义 max 3.0/3.5/4.0/4.5s 的首段实际长 3.00/3.60/4.08/4.56s，这是 120ms 块、前卷也计入缓冲及强切检查位置共同作用。最后一段可在静音结束时超过 max，例如 B 尾段 3.12s；max 并非所有分支的绝对 PCM 长度上限，未擅自改变正式语义。

A 尾段实际 1.56s，其中 VAD 语音 0.96s。它已进入 Whisper，raw 就是荷兰语，不是在线翻译把俄语改成荷兰语。尾段原始 RMS -30.885dBFS，实际增益 10.885dB；B 尾段 RMS -28.234dBFS、增益 8.234dB。归一化规则不变，但分段改变输入和实际增益，是捕获变化的伴随效应，不能声称单独隔离了上下文与增益机制。

### 猪、蚊子与疾病传播

标准原文：`Переносчиками являются свиньи, от которых через комаров болезнь затем передаётся человеку.`

流起点为 195200 帧。所有组第一段 WAV [2560,50560)，raw `Переносчиками является свиньи.`，ru/0.928149，`speech_reentry` 触发。

| max | 后段原 WAV 帧 | 后段 raw；语言/概率 | 后续处理与含义风险 |
|---|---|---|---|
| 4.5 / 3.5 / 4.0s | [50560,110080) | `от которых через Комаров болезть затем передается человеку.`；ru/0.960205 | 全文进入翻译边界；保留受传者，但普通名词成为大写 `Комаров`，此前在线记录已显示人名解释风险。本轮不调用翻译，不能声称新译文已验证。 |
| 3.0s | [50560,98560) | `от которых через комаров болезть затем передаяться`；ru/0.901237 | 小写名词恢复，但译前文本中缺少 `человеку`。自动关系匹配对 `передаяться` 这种错拼也有假阴性，不能据匹配直接裁定整句语义。 |
| 3.0s 的独立尾段 | [98560,112000)；回放流 [293760,307200) | **未进入 Whisper，raw/lang 不适用** | 捕获 0.84s，VAD 语音 0.36s、3 个 VAD 活动块；pending 后被 `asr_budget_weak_drop` 丢弃。4 次重复均复现。 |

尾段没有在 Capture 中漏帧。原 `pipeline.py::_enqueue_with_backpressure`（1186）调用 `_should_drop_weak_for_inference_budget`（1312）；弱候选在上次识别完成后 cooldown=0.35s 内被丢弃。例如 r1/5ms/B 丢弃距上一条 Whisper 完成约 224ms，队列并未积压。未把这段伪记成“Whisper 不会识别”、HTTP 超时或队列拥堵。其完整声学语义尚未单独识别或人工对齐，不能断言绕过预算后必然恢复“人”。

### 连续性、节拍与性能

68 个捕获片段、64 次流式 ASR、60 个准备翻译的片段。4 个 A 荷兰语尾段在 ASR 后过滤，4 个 B 弱尾段在 ASR 前丢弃。无合并发生；工具的合并追踪由单测验证。全部队列/worker/feeder 正常排空和退出。

捕获片段之间无内部漏帧、重叠或重复提交，原始队列 drop=0。起止边缘未捕获的静音/低活动区仍逐窗口留有记录；不能仅用 VAD 不活动就保证这些区间绝无语义。没有实现或偷偷引入有意上下文重叠。

| 请求节拍 | max | ASR P50/P95 秒 | 每次双录音回放 CPU 秒（两轮均值） | 峰值采样 RSS MiB（两轮最大） | 出队等待 P95 ms |
|---|---:|---|---:|---:|---:|
| 5ms | 4.5 | 0.985 / 1.026 | 8.891 | 344.07 | 1.0 |
| 5ms | 3.0 | 0.987 / 1.001 | 8.750 | 343.97 | 1.0 |
| 5ms | 3.5 | 0.991 / 1.024 | 9.164 | 344.13 | 1.3 |
| 5ms | 4.0 | 0.982 / 1.009 | 8.867 | 344.61 | 1.0 |
| 100ms | 4.5 | 0.977 / 1.017 | 8.914 | 344.63 | 1.0 |
| 100ms | 3.0 | 0.984 / 1.003 | 8.867 | 343.71 | 1.0 |
| 100ms | 3.5 | 0.985 / 1.021 | 8.930 | 345.07 | 1.0 |
| 100ms | 4.0 | 0.984 / 1.017 | 8.781 | 344.39 | 0.7 |

每格 ASR 仅 8 次，P50/P95 用排序后线性插值，不代表总体性能分布；CPU 包括本地观察开销，RSS 50ms 采样从模型初始化前开始，不是操作系统峰值保证。回放 CPU 不含模型加载及整段预热。单段 ASR CPU、RSS 和等待见完整结果。无在线/字幕延迟或 FPS 数据。

**节拍限制必须保留：** 此工具按 paired 方式在 process_audio 后 sleep，而非固定相位 QTimer。名义 5ms 实际周期中位数约 15.6ms，P95 约 16.1ms；名义 100ms 实际中位数约 109.2–109.4ms，P95 约 110.8–111.4ms，最大 126.3ms。100ms 实验共出现 38 次双块拼接，5ms 组没有。这确实执行了正式“排空并拼接积压块”的代码，但不是精确 5/100ms、真实 GUI 或游戏负载证明。

即使边界和 raw 相同，窗口 VAD 统计可不同：A 的蚊子首段 VAD 语音时长在 r1 从 1.44s 变 1.68s，C 的放射性尾段从 1.68s 变 1.80s。本次未改变过滤结果，不能推及其他录音/GUI 卡顿。不能用本次相同文本断言节拍永远无影响。

## 4. 结论的证据强度

- **已证实：** 固定模型、线程、beam、前卷与 idle，仅改 max 就改变铯/碘输入边界和输出。3.0s 能恢复疑似实体，4.5s 不是无关变量；3.5/4.0s 仍错，因此不能把根因简化为“只要不等于 4.5s 就好”。
- **已证实：** B 会制造新的末尾弱候选，并被原有 cooldown 规则丢弃；这是准确率收益与语义完整性的冲突，没有可按性能挑选的合格组。
- **推断：** 切段上下文、词附近边界和归一化随边界变化共同影响自动语言判断/实体解码；本轮没有单独隔离三者。前卷固定 450ms 且 B 已恢复实体，故“必须恢复 300ms 前卷才能识别实体”不成立；仍未测量前卷的独立影响。
- **未证实：** 哪一个词的声学起止恰被切开、A 尾段是否包含完整铯音节、B 未识别尾段的完整内容、真实游戏和新录音效果。已有精确帧与片段 WAV 可供人工对齐，但没有词级金标准或双语人工验收，不能替代它们。
- **决策：** 当前不足以修改正式 RU 捕获策略。没有放松过滤、替换答案、改 ASR 参数或强行选择 CER 最低组。无需为“消灭荷兰语日志”放行低概率幻觉。

## 5. 只推荐的下一步

追加一个零 API 诊断实验：**固定 B 的配置，将已丢弃的回放流 [293760,307200)（原 WAV [98560,112000)）精确 PCM 尾段，在独立空闲 Pipeline 中识别并执行原过滤，保存 raw 和保留文本。** 这只回答“排除前一次任务 cooldown 后，这段声学输入能否识别受传者”，不是新的完整回放候选，也不把取消 cooldown 包装成已修复。

必要位置是工具的精确 PCM 重放入口（可扩展本次 `run_child`）；保持 base/INT8/beam1/CPU2/auto/增益和全部 ASR 后过滤不变。衡量 `человек/человеку` 疑似保留、语言/概率、过滤、幻觉、CPU 和耗时。若尾段不能可靠识别或原过滤仍丢弃，停止将 B 推进正式策略；后续才有理由另立任务研究强切后上下文保留。**本轮没有实施该追加实验或复杂重叠。**

本轮不建议直接修改正式文件，故无需执行运行时回退；回退本次工具提交也不会改变客户端行为。任何后续正式候选仍需未参与调参的新录音，覆盖实体、否定、数字、连续语音和噪声，并安排双语人工验收，重复回放不能充当独立样本。

## 6. 可复现命令、测试与证据

以下实际 CLI 已运行；复现时必须替换成**尚不存在**的新输出目录，旧目录会被拒绝：

```powershell
Set-Location C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/offline_russian_capture_ab.py `
  --manifest build/multilingual-online/paired-live-2026-10-27/manifest.json `
  --models-directory .models `
  --output build/multilingual-online/ru-max-only-20261027 `
  --max-speech-seconds 4.5 3.0 3.5 4.0 `
  --cadence-ms 5 100 --pre-roll-ms 450 --idle-ms 450 --rounds 2
```

本轮实际测试：

```powershell
# 工具开发阶段曾运行 12 项定向测试；最终新增 15 项均包含在下列全量执行中。
$env:QT_QPA_PLATFORM='offscreen'
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest discover -s tests -q
# Ran 567 tests in 47.471s; OK (skipped=1): 566 通过，1 跳过。
# 跳过项：未设置 VOXGO_API_ROOT 的可选本地 Telemetry Worker 联合验收。

.\.venv-win\Scripts\python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py `
  --base-ref afc33a67 `
  --output build/multilingual-online/ru-max-only-20261027-validation/en-zh-compatibility.json
# 48/48 配置比较相同；这不是新的英中真实音频质量验收。

git diff a67a6563 --exit-code -- voxgo
git diff 645c6ace --exit-code -- voxgo
# 均为空，正式运行时无意外变动。
```

新证据：`docs/testing/evidence/v0.5.3-ru-capture-ab-2026-10-27/`。`segment-review.md` 为逐段人工评审入口；每组 `result.json` 保存完整参数/活动窗口/片段/快照/性能/退出，`plan.json` 保存模型及源码指纹，`summary.json` 保存复现一致性，`test-results.json` 保存本轮而非历史测试结果。

完整日志和实际片段 WAV：`build/multilingual-online/ru-max-only-20261027/`，本机保留；151 个实验产物的 SHA256/大小/相对路径列在新证据的 `artifact-index.json`。源录音授权、FLEURS 修订、出处、CC-BY-4.0 归属等随 manifest 保留。原 paired 目录和原证据目录哈希核对不变，所有子进程正常停止；无 API、Worker、R2、push、tag、生产迁移或发布。
