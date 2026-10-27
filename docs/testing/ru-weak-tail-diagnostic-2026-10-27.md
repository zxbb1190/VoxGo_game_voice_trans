# v0.5.3 俄语弱尾段：最小离线诊断

**决策：结果2——Whisper 能识别受传者，但原有识别后过滤仍会丢弃。单独移除预算丢弃不能恢复正式字幕，原样 3.0s 方案继续保持不合格，不修改 cooldown 或其他正式规则。**

## 1. 版本与范围

工作树 `C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator`，分支 `codex/multilingual-online-053`。任务开始 HEAD `5dd65ed5efe1285a737ff7c4214fc33f22b7ea2a`，工作区干净。下述正式源码位置对应 5dd65ed5；`voxgo/` 与正式运行时基准 `645c6ace` 完全相同。

本次仅新增诊断工具、8项测试、本报告及新证据。未修改既有工具、用户设置、正式代码、Telemetry、翻译或 Provider。零 API、零下载、无部署/上传/推送/发布。

## 2. 精确输入与校验

实际识别输入始终读取上一轮保存的 `build/multilingual-online/ru-max-only-20261027/r1-tick5-max3/s005.wav`；没有用重新裁切的音频替代它。

| 项目 | 校验结果 |
|---|---|
| PCM SHA256 | `5eae1b016d16a547fd91129fd379f44613f493c1a2d980f829bcdfb4b6ac5459` |
| 保存 WAV 文件 SHA256 | `5f900bafe383ca2d01d5b048a1dd24aaa722d4e1095b109041a9af1aeafd32e3` |
| 格式与长度 | mono PCM16、16kHz、13440帧、26880 PCM bytes、0.84s |
| 回放流半开区间 | [293760,307200) |
| 原 WAV 半开区间 | [98560,112000) |
| 原录音 | `fleurs-ru-holdout-1762-10098401296465388159`；已用于调研，并非新 holdout；FLEURS CC-BY-4.0 公开真实朗读，非游戏语音 |
| 原 WAV SHA256 | `6ea2ab94659f5bf289679b2e1ea091ef20275b7c2181f18d71bb1e54e3e75e90` |
| 原捕获元数据 | VAD语音0.36s、7块/3个VAD活动块、VAD比例3/7、peak −52.2796dBFS、gate −45dBFS、原丢弃 `asr_budget_weak_drop` |
| 补零/静音 | 全部区间位于原 WAV 内，回放补零0帧；自然静音、零值样本原样保留 |

同时核验旧 artifact-index 中的 WAV/result.json 文件哈希、PCM 哈希、帧数/格式，与原 WAV 区间及原回放流逐字节相同。原 WAV/回放流只用于独立校验，实际推理仍使用保存 WAV 的 PCM。

## 3. A/B执行方式

固定多语言base（缓存修订 `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`）、CPU INT8、beam1、CPU线程2、worker1、auto→Whisper `language=None`、temperature0、previous_text=False、空Prompt。配置与上一轮实际3.0s组逐字段相等；未强制ru。归一化及所有过滤参数不变。

四个独立进程依次 A/B、B/A，每个只推理这一个尾段一次，不预热其他语音：共4次真实离线推理，独立录音只有1段，不重跑原矩阵。

- **A直接识别：** `direct_then_filter` 直接调用正式 `SpeechRecognizer`（通过原观察子类采集数据）；随后用只返回此次真实结果的适配器，让正式 `SpeechPipeline._process` 执行原过滤顺序。适配器消费一次，不进行第二次推理、不修改结果。弱候选识别前检查为空；没有预算/候选等待。A的 `_process` trace ASR时间只是缓存结果交付时间，实际推理耗时必须读 `segment.asr_ms`。
- **B空闲Pipeline：** 全新 Pipeline，`last_transcription_finished_at=0`、队列0、未busy、无pending/recent transcript；不手动清零任何已有状态。保留全部原捕获元数据，调用正式 `on_speech_detected`，原worker执行等待、预算、Whisper及后过滤。不是连续现场回放，只验证“自然空闲状态下相同片段”的行为。

## 4. 原始输出与去向

四次完全一致：

```text
raw_text / text: человеку.
language: ru
language_probability: 0.7165970802307129
avg_logprob: -1.1982613801956177
no_speech_prob: 0.4966069459915161
compression_ratio: 0.68
runaway_guarded: False
```

`человеку` 与标准转写末词相符，raw中受传者疑似恢复；没有非俄语输出或重复文本。它只恢复单个受传者词，不能把“传给人”的整句关系、游戏质量或双语人工验收判为通过。

| 运行 | 是否进入Whisper | 首个实际拒绝 | 保留文本/翻译输入 |
|---|---|---|---|
| r1-A | 是，直接调用一次 | `weak_candidate_low_asr_confidence` | 均为空 |
| r1-B | 是，候选等待后调用一次 | 同上 | 均为空 |
| r2-B | 是，候选等待后调用一次 | 同上 | 均为空 |
| r2-A | 是，直接调用一次 | 同上 | 均为空 |

B被判定 `candidate,short_segment,low_confidence`；正常进入300ms pending，实测检测到处理开始为329.3/348.4ms，等待后正常入队，无 `asr_budget_weak_drop`。这与此前连续链路中的 cooldown 丢弃不同。

## 5. 具体过滤条件与风险

实际路径在 `voxgo/asr/pipeline.py::SpeechPipeline._process:756` 调用 `WeakCandidateTranscriptFilter.drop_reason:241`，于 **295行** 的 `weak_capture and weak_whisper and compact_len <= 10` 返回：

```text
weak_candidate_low_asr_confidence
(text=человеку, avg_logprob=-1.20, no_speech=0.50, compression=0.68)
```

- `weak_capture=True`：short/low_confidence 标签，语音0.36<0.7s，peak margin约−7.28<1dB等条件满足。
- `weak_whisper=True`：平均logprob −1.198<=−0.75；不是因为 no_speech>=0.55（实际约0.497）。
- 归一化后短文本 `человеку` 为8字符，满足<=10。该文本没有命中现有短指令豁免。

**实际链路到此短路，未执行后面的全局过滤或翻译入口语言门。** 另对保存的同一 ASR 结果做了不增加推理的独立只读检查，结果见 `separate-filter-checks.json`：

1. `whisper_engine.py::should_drop_transcription_result:1476` 仍会在 **1509行** 返回 `global_asr_low_logprob_short avg_logprob=-1.20`。阈值在106行为−1.10；`_is_global_short_or_suspicious_transcript:1405` 将此8字符文本判为短文本（<=12）。这不是一次实际执行路径中的第二次丢弃，而是对后续规则的独立诊断。
2. `translation/base.py::should_skip_translation_for_language:218` 独立检查无拒绝。检测ru与源ru一致，0.7166也高于0.35最低语言概率；本例并非语言概率过低造成。

因此既有链路有**预算提前丢弃、弱候选识别后拒绝、后续全局短文本拒绝**三处相关条件。仅取消 cooldown，或只绕过其中一个后过滤，都不足以让本例进入翻译边界。

已知原文的有效单词确有被通用置信度规则一并拦截的风险；但一个安静短尾段不能估计总体误过滤率，也不能证明这些规则对噪声/幻觉无价值。人工语义复核仍待完成。本轮不加该单词白名单、不放宽全局阈值。

## 6. 耗时与资源

i7-13700；每次都是独立进程的首次推理，无音频预热。

| 运行 | 实际ASR ms | 推理期间进程CPU秒 | 初始化前RSS MiB | 模型加载后RSS MiB | 峰值采样RSS MiB |
|---|---:|---:|---:|---:|---:|
| r1-A | 950.62 | 2.03125 | 73.44 | 168.60 | 333.31 |
| r1-B | 970.48 | 1.87500 | 73.97 | 169.91 | 334.79 |
| r2-B | 965.69 | 1.81250 | 73.75 | 169.71 | 334.09 |
| r2-A | 980.71 | 2.04688 | 73.59 | 168.97 | 333.45 |

RSS每20ms采样；CPU为进程CPU增量，含观察开销，不是线程独占计时。首次推理/模型惰性分配不能作为现有热进程增加一个尾段的精确增量成本，也没有测量游戏/FPS、真实字幕或低配性能。

四次归一化一致：输入/输出RMS都是 **−58.1793dBFS**，实际增益0dB，归一化float32 SHA256均为 `71a52a0f33d6314ac7a68ff5dd7a1f839c4a60c31e084402f80b68e0e65b9f88`。原规则对低于−50dBFS的音频不补增益，本轮原样保留这一行为，没有为了通过本例提高音量。

## 7. 对3.0s策略的决策与唯一下一步建议

音频有可识别的受传者信息；Whisper四次都识别成功，但正式后过滤没有保留。结果属于**结果2**，不是“尾段无内容”，也不是“Pipeline已经恢复”。原样3.0s策略仍不能可靠保留句尾，停止其正式推进，不改生产 cooldown 或置信度规则。

**只建议一个追加离线实验：少量前段声学上下文是否能让尾段得到更可靠的识别置信度并通过原过滤。** 固定现有所有模型/解码/过滤设置，只比较前段追加上下文长度0与0.48s，不改变捕获器的 pre_roll_ms。原0.84s尾段保持不动；新增组取前段末7680帧，与尾段拼接为新的PCM输入（原WAV [90880,112000)，流 [286080,307200)，1.32s），单独标注SHA和“新增上下文”，不得再称为原样尾段重放或纯预算修复。

使用原活动窗口重建新增输入的捕获元数据，不能手工标为强候选以绕过过滤；测量 raw/保留的受传者、avg_logprob、实际过滤、重复上下文、CPU和耗时。如果依然丢失受传者、被原过滤拒绝或引入重复/幻觉，停止该候选。本轮**没有执行**此实验，也没有实现正式重叠/去重算法。

## 8. 工具、测试、产物与复现

- 新增 `scripts/diagnose_russian_tail.py`：`load_tail:32` 校验原输入，`direct_then_filter:99` 执行A，`run_idle:114` 执行B，`run_child:133` 复用原观察器/真实Pipeline及退出记录。没有改动其他脚本或 `voxgo/`。
- 新增 `tests/test_diagnose_russian_tail.py`：8项测试。包含输入篡改拒绝、精确输入、A只推理一次、B原pending/停止、拒绝非空闲状态且不清零、真实低置信度结果A/B同样拒绝、全局过滤独立检查、无文本补写。
- 本轮45项相关测试全部通过；包括8项新工具、15项既有离线工具、多语言profile和ASR输出过滤测试。英中48组配置比较全部相同。**本轮未重跑完整客户端/Worker联合测试，不将上一轮记录算作本轮测试。**
- 四进程队列/pending/worker/sampler全部停止并排空；配置、模型及原始证据哈希不变；网络/Analytics尝试0、实际API0。正式 `git diff 645c6ace -- voxgo` 为空。

实际执行命令（再次运行必须使用新的不存在的输出目录）：

```powershell
Set-Location C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/diagnose_russian_tail.py `
  --source-run build/multilingual-online/ru-max-only-20261027/r1-tick5-max3 `
  --models-directory .models `
  --output build/multilingual-online/ru-tail-diagnostic-20261027

.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest `
  tests.test_diagnose_russian_tail tests.test_offline_russian_capture_ab `
  tests.test_multilingual_speech_profiles tests.test_asr_output_filter -q
# Ran 45 tests in 0.835s; OK

.\.venv-win\Scripts\python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py `
  --base-ref afc33a67 --output build/multilingual-online/ru-tail-diagnostic-20261027/en-zh-compatibility.json
# 48/48 equal；配置兼容，不是新的英中音频质量验收。
```

新证据目录：`docs/testing/evidence/v0.5.3-ru-tail-diagnostic-2026-10-27/`，含四次完整result/events、summary、原输入来源与参数、独立后续过滤检查、测试记录及产物哈希。完整本地日志和原样输出WAV在 `build/multilingual-online/ru-tail-diagnostic-20261027/`；不覆盖上一轮任何证据。
