# VoxGo ASR 三路径专项实验（2026-09-30）

## 代码和验证状态

- 已存在的基准路径：`whole`、`capture_cut`。
- 当前源码已修、已测试、已提交：下一句起音切段和 runaway repetition guard，提交 `0752e6d3`。本轮相关单元测试 89 项通过。
- 当前源码已新增、已测试、已提交：按真实时间回放的 `full_pipeline`，使用真正的 `SystemAudioCapture`、`SpeechPipeline.start()` 工作线程、队列、识别及输出过滤；自然语音准备工具及报告字段，提交 `a5f75e70`。
- 下表来自独占进程的 Benchmark；各组运行均核对失败数与 SNR×路径样本数。**没有发布新版本，也没有真实玩家语音验证**。这些源码改动不等于 0.5.1 用户已受益。

## 数据和方法

- 真人朗读语音：[OpenSLR SLR12 LibriSpeech test-clean](https://www.openslr.org/12/)（CC BY 4.0），官方压缩包 MD5 `32fa31d27d2e1cad72775fee3f4849a9` 已核对。120 条、40 位说话人；按参考词数分为短句 30、普通句 60、较长句 30。它不是自发游戏对话，也没有口音标签。
- 真人会议对话：[University of Edinburgh AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/download/) 的 [Hugging Face `edinburghcstr/ami` `ihm/test` 预切片](https://huggingface.co/datasets/edinburghcstr/ami)，来源标注 CC BY 4.0。独立选取 30 条、12 场会议、16 位说话人，短句/普通句/较长句各 10 条。参考文本含犹豫词和口语不流畅现象；样本数较小，不与 LibriSpeech 合并算总分。没有逐条口音标签。
- 每条真人语音另用现有混音器生成 20 dB 和 0 dB 两版，两个语料合计 150 条原声、450 条音频。背景是本地合成高斯噪声，不是游戏枪声、Discord 音源或真实开黑录音。每条音频独立重置捕获噪声校准及 Pipeline 状态。
- 游戏短句单独使用 30 条 Windows SAPI 合成报点，每条有 clean、20 dB、0 dB 版，共 90 条；仅作配置回归参考。
- 三路径每条音频均使用 Prompt off。`whole` 是整段 Whisper；`capture_cut` 是正式 `SystemAudioCapture` 切段后逐段 Whisper；`full_pipeline` 按真实时间送入音频块，由正式 `SpeechPipeline` 工作线程处理候选合并、队列、Whisper 与输出过滤。其余 app UI、翻译和连续多轮游戏会话不在本基准内。
- WER 忽略大小写和标点；规范化 WER 另统一数字与撇号，便于和旧报告对照。漏词率按参考词数加权。耗时是**每条音频的 ASR 调用时间总和**，不包含切段、候选等待、排队、翻译或显示时间；不是端到端延迟。P50/P95 也基于此字段。
- 为避免并行 ASR 进程干扰工作线程的队列和耗时，八组配置分别独占运行，合计 **3690 条路径记录、零失败**。LibriSpeech 三路径各 1080 条路径记录、同 preset 纯模型控制组 360 条；AMI 三路径各 270 条、纯模型控制组 90 条；SAPI 游戏短句三路径各 270 条。每个语料内部的 manifest、音频和实现哈希一致；每条 `capture_cut` 与 `full_pipeline` 的捕获片段数一致。AMI 的具体选择行号和来源元数据保存在 `docs/evaluations/ami-selection-2026-09-30.json`，音频与报告不纳入 Git。

## LibriSpeech 真人朗读：三路径准确率

每个单元为 **普通 WER / 规范化 WER**；每个 SNR 与路径均有 120 条同源语音。

| 配置 | 音频 | whole | capture_cut | full_pipeline |
| --- | --- | ---: | ---: | ---: |
| base.en / fast | clean | 6.53% / 6.14% | 14.70% / 14.30% | 14.36% / 13.91% |
| base.en / fast | 20 dB | 8.22% / 7.83% | 15.54% / 15.20% | 14.25% / 13.91% |
| base.en / fast | 0 dB | 35.53% / 35.14% | 55.97% / 55.57% | 54.22% / 53.77% |
| small.en / balanced | clean | 3.77% / 3.49% | 8.84% / 8.45% | 8.50% / 8.16% |
| small.en / balanced | 20 dB | 4.28% / 4.11% | 8.33% / 8.00% | 9.01% / 8.73% |
| small.en / balanced | 0 dB | 23.42% / 23.09% | 34.07% / 33.56% | 33.22% / 32.83% |

按规范化 WER 百分点作受控分解：

| 配置 | 音频 | `capture_cut − whole` | `full_pipeline − capture_cut` | 相对 clean 的 `whole` 噪声增量 |
| --- | --- | ---: | ---: | ---: |
| base.en / fast | clean | +8.16 | −0.39 | — |
| base.en / fast | 20 dB | +7.38 | −1.30 | +1.69 |
| base.en / fast | 0 dB | +20.44 | −1.80 | +29.00 |
| small.en / balanced | clean | +4.96 | −0.28 | — |
| small.en / balanced | 20 dB | +3.89 | +0.73 | +0.62 |
| small.en / balanced | 0 dB | +10.47 | −0.73 | +19.60 |

`whole` 的噪声增量衡量模型接收到受控加噪音频后的退化，不能单独归因于模型结构；切段与 Pipeline 增量是在同一音频、同一模型配置上比较。0 dB 时两类误差都很大：Fast 的整段噪声增量 +29.00 点，额外切段损失 +20.44 点；Balanced 分别为 +19.60 和 +10.47 点。正式 Pipeline 净追回幅度有限，而且 Balanced 在 20 dB 时反而增加 0.73 点。

自然语音 clean 的 `capture_cut` 比 `whole` 多错词，并非只吞句首。一条完整识别准确的 `librispeech-8224-274381-0011` 经切段后追加了 “I'm not sure if I'm going to do this”；Pipeline 过滤此误报。相反，`librispeech-1284-1181-0009` 在 Balanced 下 `capture_cut` 完整识别，却在 Pipeline 队列中丢失句尾 “the fire”。这说明过滤可去幻觉，也可能漏词。

## AMI 真人会议对话：独立三路径准确率

每个单元仍为 **普通 WER / 规范化 WER**；每个 SNR 与路径均为同一批 30 条对话切片。其参考文本常含 `UH`、`UM`、重启的词组及非完整句，不能将绝对 WER 与有声书直接合并。

| 配置 | 音频 | whole | capture_cut | full_pipeline |
| --- | --- | ---: | ---: | ---: |
| base.en / fast | clean | 24.28% / 23.70% | 29.48% / 28.32% | 33.53% / 32.37% |
| base.en / fast | 20 dB | 26.59% / 26.01% | 33.53% / 32.66% | 38.73% / 38.15% |
| base.en / fast | 0 dB | 68.50% / 67.63% | 83.53% / 82.95% | 80.35% / 79.77% |
| small.en / balanced | clean | 22.25% / 21.68% | 23.99% / 23.41% | 27.17% / 26.59% |
| small.en / balanced | 20 dB | 27.17% / 26.59% | 33.82% / 32.95% | 36.42% / 35.84% |
| small.en / balanced | 0 dB | 55.20% / 54.34% | 63.58% / 63.01% | 65.03% / 64.45% |

规范化 WER 的 `capture_cut − whole` 分别为 Fast **+4.62/+6.65/+15.32 点**、Balanced **+1.73/+6.36/+8.67 点**（clean/20 dB/0 dB）；`full_pipeline − capture_cut` 分别为 Fast **+4.05/+5.49/−3.18 点**、Balanced **+3.18/+2.89/+1.44 点**。因此 Pipeline 在对话的干净/轻噪声下有额外损失，不能概括为“候选合并会修复裸切段”。例如 clean `AMI_ES2004d_H01_FEE013_0155625_0156026`：裸切段保留了 “they like something that's”，正式队列丢弃一段后漏掉该词组。AMI Fast 在 clean/20 dB/0 dB 分别有 13/17/18 次队列丢弃，Balanced 有 12/14/12 次；这些是运行时事件总数，不等于错词数。

两种配置的 AMI 整段 `whole` 从 clean 到 0 dB 分别恶化 **+43.93** 和 **+32.66 点**，说明强噪声在进入实时切段前就产生了主要退化。AMI 条数只有 30，且非游戏音频，适合验证方向，不宜据此估计真实玩家总体 WER。

## 纯模型对照与耗时

额外的 `base.en/balanced/whole` 控制组与 `small.en/balanced/whole` 使用相同 360 条音频、CPU int8、2 线程、beam 1、Prompt off，零失败。规范化 WER 为：

| 音频 | base.en | small.en | small.en 少错 | 整段平均 ASR 耗时 base → small |
| --- | ---: | ---: | ---: | ---: |
| clean | 6.14% | 3.49% | 2.65 点 | 0.54s → 1.70s |
| 20 dB | 7.83% | 4.11% | 3.72 点 | 0.53s → 1.72s |
| 0 dB | 35.14% | 23.09% | 12.05 点 | 0.53s → 1.74s |

AMI 也用相同 90 条音频、相同 Balanced 配置单独做整段模型控制，规范化 WER 为：

| AMI 音频 | base.en | small.en | small.en 少错 | 整段平均 ASR 耗时 base → small |
| --- | ---: | ---: | ---: | ---: |
| clean | 23.70% | 21.68% | 2.02 点 | 0.54s → 1.59s |
| 20 dB | 26.01% | 26.59% | −0.58 点 | 0.50s → 1.59s |
| 0 dB | 67.63% | 54.34% | 13.29 点 | 0.51s → 1.59s |

两个真人语料均显示 0 dB 下 `small.en` 整段少错约 12–13 点；干净/轻噪声收益随语料变化，AMI 的 20 dB 甚至略差。CPU 平均推理约为 `base.en` 的 3 倍。模型升级也没有消除 `small.en/balanced` 自身的切段与 Pipeline 损失。

LibriSpeech **0 dB** 的分层耗时和片段统计：

| 配置 / 路径 | ASR 平均 / P50 / P95 | 平均送识别片段数 | 平均识别片段时长 | Pipeline 过滤 / 队列丢弃 | 漏词率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| base.en / fast / whole | 0.88 / 0.87 / 0.99s | 1.00 | 5.69s | — | 3.83% |
| base.en / fast / capture_cut | 2.38 / 1.85 / 4.93s | 2.88 | 2.09s | — | 5.24% |
| base.en / fast / full_pipeline | 2.12 / 1.67 / 4.16s | 2.55 | 2.28s | 33 / 37 | 8.16% |
| small.en / balanced / whole | 1.74 / 1.68 / 2.10s | 1.00 | 5.69s | — | 2.08% |
| small.en / balanced / capture_cut | 3.23 / 3.16 / 6.49s | 1.93 | 3.21s | — | 6.48% |
| small.en / balanced / full_pipeline | 2.99 / 3.11 / 6.54s | 1.78 | 3.39s | 16 / 17 | 7.09% |

Pipeline 的 ASR 耗时较低可能源于过滤或丢弃部分片段，**不代表端到端更快**。两种真人语料的最终文本均无失控重复；强噪声下仍有原始重复由 guard 拦截。Prompt 泄漏计数为零，但本轮只测试了 Prompt off，因而不能评判 game_en 的泄漏风险或收益。

AMI 0 dB 的平均/P50/P95 ASR 调用总耗时分别为：Fast `whole` **0.86/0.85/0.97s**、`capture_cut` **2.47/2.46/5.09s**、`full_pipeline` **1.83/1.65/3.34s**；Balanced 分别为 **1.59/1.57/1.79s**、**3.37/3.06/6.98s**、**2.77/3.04/5.47s**。平均送识别片段数 Fast 为 **1.00/2.90/2.17**，Balanced 为 **1.00/2.20/1.80**；对应平均片段时长 Fast 为 **4.62/1.55/1.79s**，Balanced 为 **4.62/2.18/2.39s**。AMI 的 Pipeline 在 0 dB 比裸切段的漏词率更高：Fast **15.32%→38.44%**，Balanced **21.39%→33.82%**，部分误报减少但丢候选增加。

## SAPI 游戏短句：单独的回归结果

每个 SNR 有 30 条合成短句。下表为规范化 WER / 规范化整句命中率（`whole → capture_cut → full_pipeline`）：

| 配置 | 音频 | whole | capture_cut | full_pipeline |
| --- | --- | ---: | ---: | ---: |
| base.en / fast | clean | 0.59% / 96.7% | 1.78% / 93.3% | 4.14% / 86.7% |
| base.en / fast | 20 dB | 1.18% / 93.3% | 1.18% / 93.3% | 5.33% / 86.7% |
| base.en / fast | 0 dB | 13.02% / 50.0% | 21.89% / 23.3% | 13.61% / 46.7% |
| small.en / balanced | clean | 1.78% / 93.3% | 1.78% / 93.3% | 4.14% / 86.7% |
| small.en / balanced | 20 dB | 0.59% / 96.7% | 0.59% / 96.7% | 2.96% / 90.0% |
| small.en / balanced | 0 dB | 8.28% / 56.7% | 8.28% / 56.7% | 8.28% / 56.7% |

SAPI 的 Balanced 切段在三档均接近 `whole`，但真人朗读语音并非如此。Fast 的 SAPI 0 dB 由 Pipeline 追回大部分裸切段损失，却发生 15 次队列丢弃；Pipeline 在干净/轻噪声下反而漏掉若干有效游戏短句。因此不应以 SAPI 总分决定真实玩家默认值。

## 判断与下一步

本次受控数据支持**混合因素**：强噪声使整段识别本身明显变差，实时切段再增加可观错误；正式 Pipeline 的净影响依语料和噪声而变，LibriSpeech 大多追回不到 2 点，AMI 对话的 clean/20 dB 却额外损失 2.89–5.49 点，且有实际过滤和队列丢弃。自然语音上，Fast 和 Balanced 都不能称为切段无损。`small.en` 的模型能力在 0 dB 下确有收益，但 CPU 推理约 3 倍。本轮 Prompt off，不能将问题归因于 Prompt。

下一项有直接数据支持的工程实验是**针对实时切段及正式 Pipeline 的候选队列/输出过滤做有界 A/B**，优先回放本报告中 `whole` 正确但 `capture_cut/full_pipeline` 变差的自然样本，并在真实时间压力下单独追踪丢候选；Fast 的 0 dB 差距最大，同时 AMI 证明 Balanced 也非无损。保持产品默认值不变。0 dB 的整段退化还提示需在取得明确同意的真实玩家游戏录音上验证音源混杂，再决定是否值得做前置降噪或 Audio Session 分离。合成高斯噪声、朗读和会议语音不足以给真实游戏环境的单一主因下结论，也不能支持立即发布或默认升级 `small.en`。

## 本机详细报告

原始逐条文本、WER 分解、P50/P95、片段、候选过滤、队列丢弃、原始重复及失败列表位于（本机忽略目录，不随 Git 提交）：

- `diagnostics/asr-benchmark/natural-fast-isolated/report.html` / `report.json`
- `diagnostics/asr-benchmark/natural-balanced-isolated/report.html` / `report.json`
- `diagnostics/asr-benchmark/natural-base-balanced-control/report.html` / `report.json`
- `diagnostics/asr-benchmark/game-fast-isolated/report.html` / `report.json`
- `diagnostics/asr-benchmark/game-balanced-isolated/report.html` / `report.json`
- `diagnostics/asr-benchmark/ami-fast-isolated/report.html` / `report.json`
- `diagnostics/asr-benchmark/ami-balanced-isolated/report.html` / `report.json`
- `diagnostics/asr-benchmark/ami-base-balanced-control/report.html` / `report.json`

之前按串行方式排空队列的离线 `full_pipeline` 诊断结果，以及多组 ASR 同时运行时的报告，不用于以上 Pipeline 准确率和延迟结论；它们保留在本机供排查。已有的修复后 Benchmark 基线报告也原样保留。
