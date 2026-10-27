# v0.5.3 俄语短尾段：0 / 0.48s声学上下文最终定向实验

**结论：新增0.48s上下文只改善置信度数值，没有改变raw文本，也没有恢复译前输入。停止围绕此样本调整上下文长度；原样3.0s策略和专用上下文恢复机制均不进入正式客户端。**

## Git、工具与范围

开始版本 `3a56f25d58e9786f98fa317a24fd225ce43511b4`，分支 `codex/multilingual-online-053`，工作树 `C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator`，开始时干净。正式 `voxgo/` 相对开始版本及 `645c6ace` 均零差异。

只扩展 `scripts/diagnose_russian_tail.py` 和其测试，新增本报告/新证据；没有第二套Whisper或Pipeline实现。`--context-ab` 使用既有 ObservedRecognizer/ObservedPipeline，每组独立新进程两次，顺序A/B、B/A，共**4次真实推理，1段已用于调研的独立ASR录音**。不另外做直接识别或音频预热；ASR层指标从同一次真实Pipeline推理中观察，后处理独立检查只调用原过滤函数，不再推理。

新工具函数：`metadata_from_windows:134`、`context_pcm:152`、`context_input:167`、`overlap_review:219`；`run_child:236` 复用原空闲Pipeline。旧的默认直接识别/空闲Pipeline诊断入口保留。新增6项上下文工具测试。

## PCM与固定参数

源录音仍为FLEURS俄语公开真实朗读 `fleurs-ru-holdout-1762-10098401296465388159`，不是新holdout或游戏语音；原文件SHA256和CC-BY-4.0归属随证据保留。

| 组 | 原WAV帧区间 / 回放流帧区间（半开） | 输入帧数/时长 | PCM SHA256 |
|---|---|---|---|
| A 原尾段 | [98560,112000) / [293760,307200) | 13440 / 0.84s | `5eae1b016d16a547fd91129fd379f44613f493c1a2d980f829bcdfb4b6ac5459` |
| B **新增上下文** | [90880,112000) / [286080,307200) | 21120 / 1.32s | `4af960758c23c1ec93ef73cde01cdbdaf326c2fd0e9b4872ba625b7f19e237ed` |

A继续使用已保存 `r1-tick5-max3/s005.wav` 的PCM；B由原WAV重建。B末尾13440帧与A逐字节一致。两组均为16kHz mono PCM16，未调音量/采样率、未移除自然静音、未增加回放补零。模型是同一缓存多语言base修订 `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`；4项模型文件指纹与现存缓存及各进程一致，完整SHA256在plan/result中。

实际配置逐字段与原3.0s组相同：CPU INT8、beam1、线程2、worker1、auto→None、temperature0、previous_text=False、空Prompt；原归一化、语言/弱候选/全局过滤均未改变。捕获配置仍3.0s / pre_roll_ms450 / idle450，不把声学前置上下文冒称修改正式前卷。

## 元数据与Pipeline的真实性边界

工具用正式 `SystemAudioCapture` 按原1920帧（120ms）块顺序，只读重放原流以恢复WebRTC VAD/噪声门状态。它精确复现了旧实验的全部捕获片段、边界及捕获元数据，并核对A派生字段逐项一致。原流中的放射性录音仅用于恢复捕获状态，**没有对它进行ASR**。这不是重跑原矩阵，也不是物理音频回放。

活动计数来自正式捕获器实际进入活动分支的窗口；峰值只取活动窗口。B不是复制A或手工标成强候选：

| 项目 | A | B |
|---|---:|---:|
| VAD语音时长 | 0.36s | 0.72s |
| 窗口/VAD活动窗口 | 7 / 3 | 11 / 6 |
| VAD confidence | 0.428571 | 0.545455 |
| peak / gate dBFS | −52.2796 / −45 | −51.5827 / −45 |
| 正式候选分类 | short_segment、low_confidence | short_segment、low_confidence |

两组进入全新空闲Pipeline，未手动清零已有状态。均经过原300ms候选等待、正常入队并进入Whisper；A实际待处理约336–338ms，B约327–328ms，没有预算丢弃或新队列积压。

**B是实际窗口元数据支持的诊断性拼接输入，当前正式捕获器不会自动发出该前置上下文片段。** 这里只验证该输入在真实空闲Pipeline中的行为，不声称连续生产 Capture→Pipeline 已完整通过；原连续链路的cooldown问题也没有被修复。

## ASR与过滤结果

各组两次raw、全部ASR数值和过滤结果完全一致：

| 指标 | A | B |
|---|---|---|
| raw / text | `человеку.` | `человеку.` |
| language / probability | ru / 0.7165970802 | ru / 0.8775906563 |
| avg_logprob | −1.1982613802 | −1.0070051750 |
| no_speech_prob | 0.4966069460 | 0.2064390182 |
| compression_ratio | 0.68 | 0.68 |
| 非俄语/重复失控 | 未见 / False | 未见 / False |
| **实际首个拒绝** | weak_candidate_low_asr_confidence | weak_candidate_low_asr_confidence |
| **最终保留文本/译前输入** | 空 / 空 | 空 / 空 |

触发原 `WeakCandidateTranscriptFilter.drop_reason`（`voxgo/asr/pipeline.py:241`，295行分支）：两组仍为弱候选，avg_logprob均<=−0.75，归一化短文本8字符<=10。B没有通过该规则。语言概率不是这次拒绝原因。

实际路径到此短路。另对保存结果独立调用原后续过滤：A会触发 `global_asr_low_logprob_short`；B不会触发该全局规则（−1.007>−1.10），翻译入口语言门两组均无拒绝。这些独立检查没有放行文本，也不是实际Pipeline越过了第一处拒绝。

**不同长度输入的avg_logprob不是质量分数。** 输入声学证据/有效语音比例改变，即使输出token相同，其条件概率也会变化；不能用−1.198→−1.007证明语义改善。两组归一化实际增益都为0dB，RMS由−58.1793变为−55.9631dBFS来自原声学上下文，而非人为放大。raw内容及送译结果没有改善。

## 重复、拼接与语义风险

原前段raw：`от которых через комаров болезть затем передаяться`

两组仅用于评测的原样串联完全相同：

```text
от которых через комаров болезть затем передаяться человеку.
```

B未重复已有动词/短语；精确后缀-前缀重复token数为0，边界模糊对齐无命中。未实现正式去重，没有补写/替换输出。该样本未见新增实体/否定冲突（AI辅助，人工待核验），但B也没有纠正前段的 `болезть`、`передаяться` 等词形错误，简单串联没有比A更接近完整原意。

受传者在A的raw中已经存在，B没有新增恢复内容。上述串联是分析材料；实际两组尾段均未保留，不能把这条串联当成真实送译文本或字幕。单例未重复也不能证明其他上下文不会重复。

## 性能与资源

i7-13700，每次独立进程首次推理，无音频预热；CPU/RSS含观察器开销，峰值RSS每20ms采样。捕获元数据重放在推理计时之前完成。

| 运行 | ASR ms | 推理期间进程CPU秒 | 峰值采样RSS MiB |
|---|---:|---:|---:|
| r1-A | 949.88 | 1.84375 | 340.14 |
| r1-B | 969.50 | 1.92188 | 342.14 |
| r2-B | 960.35 | 1.92188 | 343.86 |
| r2-A | 962.20 | 1.85938 | 341.89 |

两次均值：A/B约956.04/964.93ms，CPU约1.85156/1.92188秒；观察差约+8.89ms、+0.07031 CPU秒。样本太少且都是首次推理，不构成有统计意义的性能差异或热运行增量成本，也没有游戏/FPS、在线翻译或真实字幕延迟数据。

## 四层结论与唯一下一步

- **当前样本改善：** 只有置信度数值改善；raw不变、译前输入仍空，目标未达到。
- **机制可行性：** 能构造可追溯上下文并做诊断Pipeline验证；有用的“通过原过滤并恢复译前语义”机制尚未证明，不足以优先开发专用恢复机制。
- **泛化证据：** 无新的独立录音；重复两次只说明本例确定性，不能支持泛化。
- **发布标准：** 不满足。正式代码和原样3.0s策略均不改，不放宽阈值，不继续0.24/0.72/0.96s或网格搜索。

**下一步只推荐：建立新的独立俄语连续录音分段语义完整性回归集，作为通用分段/短尾段保留策略的开发依据。** 覆盖实体、否定、数字、连续发言与噪声，保留未调参样本及人工复核；先比较实际边界与关键语义保留，不基于本例分数改善启动正式声学上下文恢复功能。本样本的定向实验到此结束。

## 本轮测试、复现与证据

```powershell
Set-Location C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/diagnose_russian_tail.py --context-ab `
  --source-run build/multilingual-online/ru-max-only-20261027/r1-tick5-max3 `
  --models-directory .models --output build/multilingual-online/ru-tail-context-20261027
# 已执行；再次复现必须换成不存在的新输出目录。

.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest `
  tests.test_diagnose_russian_tail tests.test_offline_russian_capture_ab `
  tests.test_multilingual_speech_profiles tests.test_asr_output_filter -q
# Ran 51 tests in 0.841s; OK（本轮新增6项）。

.\.venv-win\Scripts\python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py `
  --base-ref afc33a67 --output build/multilingual-online/ru-tail-context-20261027/en-zh-compatibility.json
# 48/48配置比较相同；不是新的英中音频质量验收。
git diff 3a56f25d --exit-code -- voxgo
git diff 645c6ace --exit-code -- voxgo
# 均为空。本轮未重跑完整客户端/Worker联合测试。
```

新证据：`docs/testing/evidence/v0.5.3-ru-tail-context-2026-10-27/`，含完整四次result/events、模型/PCM指纹、`context-analysis.json`组内稳定性及独立过滤检查、`verification.json`、测试记录。旧summary中跨全部四次比较的字段为False是A/B概率不同，不能误读为组内重复不稳定。

完整本地日志、A/B输入WAV及捕获状态复现窗口/片段在 `build/multilingual-online/ru-tail-context-20261027/`，哈希清单在新证据 `artifact-index.json`。单独的零推理元数据预检保存在 `build/multilingual-online/ru-context-metadata-preflight-20261027/`。

四进程全部排空，worker/sampler停止；配置、模型、旧实验及证据未变。网络/Analytics尝试和真实API均0，未接触生产、下载、部署、上传、push、tag或发布。
