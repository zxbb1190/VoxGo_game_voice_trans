# 俄语连续语音独立基线（2026-10-27）

结论：离线数据规范、回放入口和两种既有策略的基线已经建立；**数据覆盖与人工真值仍未完成，不能据此宣布俄语发布质量或策略胜出**。本轮没有调整识别算法。

## 1. 版本与三份核心交付

- 分支 `codex/multilingual-online-053`；采集运行 HEAD `26e646bcf15411c6b30d58ea6118a4d5625bb7a9`，正式运行时基准 `645c6ace`。
- 开始时该 worktree 干净；本轮只改实验工具、工具测试和文档。`git diff 645c6ace -- voxgo` 为空。原主工作区未切换分支、未清理。
- [数据 Manifest](evidence/v0.5.3-ru-continuous-2026-10-27/dataset-manifest.json)：36 个源文件的来源、版本、许可、转写状态、分组、WAV/PCM SHA256。
- 本报告：实际基线、统计边界与复现命令。
- [下一阶段建议](ru-continuous-next-2026-10-27.md)：根据新样本回答优化决策，不沿用旧两条录音推断。

## 2. 实际取得的数据与缺口

| 分组 | 独立源文件数 | 时长 | 本轮推理 | 人工状态 |
|---|---:|---:|---|---|
| dev | 16 | 226.80s | 两种策略各一次 | 转写覆盖、逐词边界、语义均 pending |
| locked_holdout | **0** | 0 | 禁止 | 尚未建立合格的说话人隔离 |
| quarantine（拟验收） | 8 | 102.68s | **0 次** | 仅清单与哈希；不是已验证 holdout |
| negative | 12 | 123.38s | 两种策略各一次 | 供应方 noise 标签；人工无语音确认 pending |

**不能把 56 次进程运行当作 56 条独立语音**：实际评测为 16 条语音与 12 条负样本各两个策略，不重放取最好结果，也没有调参矩阵。

语音来自 [PolyAI/MInDS-14 固定版本](https://huggingface.co/datasets/PolyAI/minds14/blob/40ce77cb32a384e4d50a568e1ec39ac804019d33/README.md)，CC-BY-4.0，署名 Daniela Gerz 等 / PolyAI / 源贡献者。版本 `40ce77cb32a384e4d50a568e1ec39ac804019d33`。这是实际单源录制的众包银行业务发言，原始 8kHz，非游戏、非拼接朗读。选择在推理前冻结：来源转写不少于 18 词，按 intent 轮询选取 24 个不同源文件，前 16 个 dev，后 8 个隔离。

该来源**没有说话人或会话 ID**。全部未知说话人归为一个保守组 `minds14:unknown-all`，未知会话亦视为一个组，不能声称取得 24 名不同说话人或满足 dev/holdout 身份隔离。工具禁止未知身份数据升级为已验证 locked 集；即使新增另一来源的已知说话人，dev 身份仍未知时也不会自动认证隔离。

负样本来自 MUSAN 的 FreeSound noise 0000–0011，每个源文件仅取开头最多 12s，保留裁取区间。采用 [该子集明确的 Public Domain 来源声明](https://huggingface.co/datasets/corypaik/musan/blob/76f9882cfa4475efe11508ac9aa32722f84ca5b7/licenses/noise/free-sound/LICENSE)，固定镜像版本 `76f9882cfa4475efe11508ac9aa32722f84ca5b7`；署名 MUSAN（David Snyder、Guoguo Chen、Daniel Povey）及 FreeSound 贡献者。未将 MUSAN 中许可不同的其他音频一并使用。

新增下载账本合计 **11,810,041 bytes（11.81MB）**，上限 100,000,000 bytes；保留失败下载计数，未下载模型。许可证原文保存在证据目录。数据服务生成的临时音频 URL 仅留在本地来源缓存，未提交；账本去除了 query，保留请求 URL 哈希。来源仓库版本在获取后复核；复现以实际下载原文件及转换后 PCM 哈希为准，不假定未来数据服务排序/临时 URL 永远不变。

历史清点覆盖 282 份证据 JSON、297 个不同哈希，识别 9 条已使用 FLEURS RU 源文件，含旧称 holdout 的蚊子传播样本，全部保留为历史数据。未确认存在可直接使用的本地新 RU 录音。新 36 个 WAV/PCM 均无历史哈希匹配；这是项目证据范围内的新颖性检查，不能证明说话人独立或模型训练集排除。

覆盖不足必须保留：没有人工确认的多句/快速/重叠语音标签，没有真实游戏、噪声语音正样本和专门的短尾音组；16 条 dev 的来源文本中有 4 条包含简单否定词，但 **0 条包含阿拉伯数字**，不能据此验收数字识别。数词、地名、人名、关系与句尾标签仍为空且状态 pending。后续需要另建有身份与授权证据、含目标场景的语料版本。

## 3. 复用的真实链路与观测能力

没有新增另一套 Whisper 调用。新入口注入单文件 PCM 和通过正式配置解析器生成的配置，复用 `scripts/offline_russian_capture_ab.py:218 run_child`，原有矩阵入口默认行为保留。

```text
16k mono PCM16 文件（前后各补 3s 零；原内容不改）
  -> ObservedCapture.feed / SystemAudioCapture.process_audio
  -> 正式 _emit_speech_buffer / SpeechSegment
  -> SpeechPipeline.on_speech_detected（候选、等待、预算、队列）
  -> SpeechPipeline._process
  -> SpeechRecognizer.transcribe_audio_bytes_with_language
  -> 正式归一化、自动语种、弱候选/全局过滤
  -> TranscriptReady + 与 app 相同的语言门
  -> 记录真实译前输入（到此结束；无 Provider、HTTP 或字幕显示）
```

核心位置：`voxgo/audio/capture.py:999 process_audio`、`:1266 _emit_speech_buffer`；`voxgo/asr/pipeline.py:513 on_speech_detected`、`:629 _process`、`:1312 _should_drop_weak_for_inference_budget`；`voxgo/asr/whisper_engine.py:949 transcribe_audio_bytes_with_language`。这些运行时代码与 `645c6ace` 一致。

| 能力 | 本轮状态及实现 |
|---|---|
| PCM、模型、环境指纹 | 复用 `offline_russian_capture_ab.local_base/fingerprint`，增加来源原文件/WAV/PCM SHA 校验 |
| 帧边界、前卷、丢弃原因 | 复用 `offline_asr_observer.py:149 ObservedCapture` / `:243 ObservedPipeline`；每片段 WAV、原 WAV 交集、activity window、drop 事件 |
| raw / 保留 / 译前输入 | 复用 `ObservedRecognizer:302` 与应用语言门；v2 汇总把语言门拒绝与 ASR 后过滤分开计数 |
| 语种与真实策略注入 | `run_ru_continuous_baseline.py:23 strategy_config`；正式配置迁移、语言策略和 effective config，不手填实验参数 |
| CER/WER | 复用既有字符编辑距离、词级 DP；新增俄语 Unicode tokenizer，避免英文字母分词和英文数字归一化误用 |
| 性能 | 所有完成的 ASR（包括被过滤者）耗时/进程 CPU，队列等待、回放 CPU、采样 RSS、捕获到终态时长 |
| 语义与根因真值 | **未实现人工自动替代**；267 个去重 PCM 审阅项均未填写，已有人工字段与逐词帧标签位置 |
| 英中保护 | 既有兼容工具 48/48；正式 `voxgo/` 零差异 |

回放是独立进程中的 120ms 音频注入、处理后等待 100ms 的主循环模拟，实际 tick 保存在原始结果。不是 GUI/QTimer、真实 loopback、游戏或低配实测。观测、JSON 写盘和 WAV 保存也消耗 CPU/RSS；不能把数值当成纯 Whisper 内核成本或字幕端到端延迟。

## 4. 两种策略实际参数

| 参数 | legacy | language_aware |
|---|---|---|
| 有效模型 | multilingual base | multilingual base |
| device / compute / beam | CPU / INT8 / 1 | CPU / INT8 / 1 |
| CPU threads / workers | 1 / 1 | 2 / 1 |
| 捕获上限 / pre-roll / idle | 3.0s / 300ms / 350ms | 4.5s / 450ms / 450ms |
| 捕获 block / WebRTC VAD | 120ms / aggressiveness 2 | 相同 |
| language / Prompt / previous text | auto / 空 / False | 相同 |
| temperature / Whisper VAD | 0 / False | 相同 |
| 语言概率下限 / 译前不匹配门 | 0.35 / 0.60 + 脚本检查 | 相同 |
| 逻辑 policy queue / 实际 ASR queue / 音频 queue | 3 / 8 / 5 | 相同 |
| pending / busy weak delay / busy stale | 0.3 / 0.5 / 1.6s | 相同 |
| weak cooldown / weak stale | 0.35 / 1.6s | 相同 |
| 归一化 | 原规则：目标 RMS −20dBFS、最大增益 12dB | 相同 |

这里的 legacy 3s 是正式兼容配置，并非旧实验的 3s/450ms/2threads 组合。配置对象还含非生效的 `model_size=small` 等 UI 配置；实际加载模型由 `active_model_size=base`、本地 snapshot 和每个 work item 的 effective config 共同核实。Whisper VAD 参数虽随正式捕获上限同步，但本轮 `vad_filter=False`，不生效。全部配置及滤波结果在每个 `raw/<ID>--<strategy>/result.json` 中保存。

模型 snapshot `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`，`model.bin` 145,217,532 bytes，SHA256 `d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9`。环境：i7-13700、16 核/24 线程、约 31.75GiB RAM；Windows build 26300、Python 3.10.20、faster-whisper 1.2.1、CTranslate2 4.7.2、NumPy 1.24.3、webrtcvad-wheels 2.0.14。每条录音新进程、无整文件预识别/热身；策略顺序按录音交替 AB/BA，运行计划推理前冻结。

## 5. 统计方法和识别结果

每个独立源文件完整回放，按真实 `whisper_end` 顺序分别聚合 raw、ASR 后保留文本和译前文本；**不拿整段参考文本随意分配给流式片段**，不按参考答案重排、去重或补词。若发现重叠/重复提交/非单调推理顺序则关闭该条评分。本轮 56 条策略结果均通过这个结构检查；所有补零区产生的识别也纳入插入错误。原始 PCM 覆盖缺口单独列出，静音/VAD 未提交本身不等于语音漏帧。

字符层采用 NFKC、casefold、保留字母数字；词层采用 Unicode 字母数字 token，保留俄文，不将数字改写成英语。整录音编辑距离可观察全流程删除/插入影响，**不能定位某个词的最早错误阶段**。

以下均是对**待人工确认的来源转写**的临时 micro 编辑距离，不是已验收准确率。每条录音指标、参考文本状态和 raw/保留/译前完整文本均见 `baseline-summary.json.recordings`。人工 CER/WER、实体正确率、数字/否定语义正确率保持 null。

| dev（16 条） | legacy CER / WER | language_aware CER / WER |
|---|---:|---:|
| raw 临时编辑距离 | 34.38% / 58.29% | 61.75% / 45.73% |
| ASR 后保留文本 | 34.92% / 57.29% | 37.08% / 41.96% |
| 最终译前文本 | 33.94% / 54.52% | 26.43% / 41.21% |

候选 raw CER 被少数长重复/异语输出显著拉高；过滤移除这些内容后指标下降，不能解释成语义完整性自动提高。CER 可以超过 100%，不能用 `1−CER` 直接宣传准确率。候选译前 CER 相对较低，但也有独立录音退化；仅是一组窄领域数据的观察，不足以选择策略或证明泛化收益。

## 6. 切段、预算、过滤与负样本

| 计数 | dev legacy | dev aware | negative legacy | negative aware |
|---|---:|---:|---:|---:|
| 捕获 / 强制上限切段 | 103 / 43 | 82 / 26 | 58 / 24 | 47 / 12 |
| Whisper 尝试 / 完成 | 79 / 79 | 64 / 64 | 42 / 42 | 35 / 35 |
| 识别前丢弃（其中预算） | 24（18） | 18（12） | 16（10） | 12（7） |
| ASR 后过滤 | 11 | 14 | 40 | 34 |
| 应用译前语言门拒绝 | 4 | 4 | 1 | 1 |
| 非空译前片段 | 64 | 46 | 1 | 0 |
| raw queue 丢块 / 未排空任务 / 合并 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

预算丢弃出现在 **12/16** 条 legacy dev、**7/16** 条 aware dev 中，说明该行为并非旧样本独有；但被丢弃 PCM 尚无人工语义标注，**不能把它们全判为误杀**。其余 dev 识别前丢弃两策略各 6 个，均为 `weak_fast_pre_asr_low_confidence_tiny_voice`。

dev ASR 后原因：legacy 的 empty 5、语言概率低 3、弱候选置信度低 2、全局短文本低 logprob 1；aware 的 empty 7、语言概率低 3、弱候选置信度低 3、重复噪声 1。保留阶段不含应用语言门的 4+4 个拒绝，避免漏计或双计。`empty_asr` 还可能是原始输出被既有归一化清空，不一律等同 Whisper 从未输出。

负样本产生 raw 非空的录音为 **9/12（legacy）、10/12（aware）**；进入译前边界为 **1/12、0/12**。这说明需要同步评价误触发成本，但音频的“无可懂语音”尚待人工确认，不能称为已核实假阳性率。没有将负样本按空参考强算 CER/WER。

结构检查没有发现本次提交片段的 PCM 重叠、重复提交或推理重排；290 个片段均逐字节复核为完整回放流相应帧范围。捕获未覆盖的帧区间、捕获后未送 Whisper 的区间仍在结果中，**尚不能排除这些区间含有效短尾音**。

### 新样本审阅示例（不是人工裁决）

| ID / 观察 | 原始证据及最先可观察环节 | 尚未证实部分 |
|---|---|---|
| `minds14-ru-0110`：疑似新增否定 | 来源 `мне хотелось положить деньги…`；aware s002 raw `Не хотелось положить деньги на свойще!`，保留并进入译前。最先可观察差异在 Whisper raw，后处理没有添加该否定；legacy 同样出现额外 `Не` | 需要人工听音及逐词帧确认；不能排除切段/声学输入/上下文的上游影响 |
| `minds14-ru-0428`：候选退化 | aware s002 原 WAV `[67200,97920)` raw 为日文长重复，应用门 `text_script_mismatch:ja->ru` 拒绝；legacy 对应整录音的译前临时 CER 20%，aware 42% | 首个可见异常是 Whisper raw；不能只因片段变长便断言 Capture 根因 |
| `minds14-ru-0505`：地名与后续内容 | 来源含 `в швецию на целый месяц`；aware s003 raw `Продолжение в шеец на целомение.` 被放行。两个起始微语音段识别前拒绝，后续还有 `Merci Bonne` 弱过滤与预算丢弃 | 来源音频/参考待人工核对；Whisper、Capture、Context 可能共同相关，不能宣称只是过滤造成 |
| `minds14-ru-0503`：重复噪声被挡住 | aware s003 raw 印地文长重复，`global_asr_repeated_noise` 拒绝；末端另有两段预算丢弃 | 拦截重复是已观察行为；末尾 `Спасибо` 的实际声学位置和被丢弃原因仍需帧标注 |
| `noise-free-sound-0001`：疑似噪声漏放 | legacy 译前输入 `I'm so sorry. I'm so sorry.`；aware 译前为空 | 人工确认该源片段无对应语音之前，只标疑似，不以文字离奇代替听音 |

自动词面检查：两策略各 1 条否定 token 数不同；尾部三词不同为 14/16、13/16；数字变化标记均 0。**这些不是语义错误率**，尤其数字未覆盖、尾部词形/来源转写误差会造成假阳性。267 项人工表按录音+PCM 边界+哈希去重，包含完整录音和片段路径、raw/译前内容、拒绝原因、待填 speech_present / spoken_text / word_frame_labels / entities / negation / first_error_stage 等字段。

## 7. 性能（包含所有成功返回的 ASR，含其后被拒绝者）

| 范围 | 单段 ASR P50 / P95 | CPU 秒/音频分钟 | 峰值采样 RSS | 队列等待 P95 |
|---|---:|---:|---:|---:|
| dev legacy（79 次） | 1.646 / 1.692s | 34.66 | 344.14MiB | 1.01ms |
| dev aware（64 次） | 0.986 / 1.059s | 38.09 | 344.70MiB | 1.00ms |
| negative legacy（42 次） | 1.611 / 2.740s | 36.59 | 341.98MiB | 639.69ms |
| negative aware（35 次） | 0.961 / 1.623s | 40.48 | 343.52MiB | 1.04ms |

dev 总 CPU 为 131.00s / 143.97s，候选增加约 9.9%；候选单次墙钟更短并不代表总计算更少。线程、切段等同时不同，本轮不作单变量归因。全部 220 次 Whisper 尝试均完成，无调用失败；识别前 70 次丢弃单独统计，未伪造其 ASR 耗时，也未从统计中隐去。

CPU 分子为模型初始化之后至回放排空的进程 CPU（含观测与补零处理），分母仅原录音时长；不含模型加载，无热身。RSS 是整个子进程采样峰值，不是精确分配峰值。所有片段的捕获→丢弃/译前终态耗时另存，包含失败路径；帧→捕获时钟仅由注入时序估计，不是人声结束→字幕时延。

dev 队列 P95 近零、没有 raw queue 丢块或未排空，故目前没有把“先修队列积压”排在前面的证据。预算检查本身可因 stale 或前次完成后的 cooldown 返回 True（`pipeline.py:1312`），不以队列满为必要条件；现有单一 reason 不足以准确细分所有预算拒绝分支。

## 8. 测试、证据与复现

全量客户端 `unittest`：**598 tests，OK，1 skipped**，47.631s；跳过的是未设置 `VOXGO_API_ROOT` 的可选 Worker 联合验收，本轮无服务端变更。新增 17 项工具测试覆盖历史哈希排除、来源/说话人泄漏、未知身份不可认证 holdout、冻结配置、WAV 格式/帧数、下载限额与不覆盖、RU tokenizer、实际参数、事件顺序、过滤计数和未填写人工标签。英中兼容检查 **48/48 equal**。

独立零推理复核：36 个源文件和转换 WAV、290 个保存片段与回放流逐字节一致；56 份 v2 分析由原始事件重新计算完全相同；模型、运行时、各组生效配置匹配。56 个进程全部正常排空，worker/feeder/sampler 均停止，网络和 Analytics 导入尝试 0。用户设置未读取或写入，API 请求 0。

主目录（本 worktree 下）：

- `build/multilingual-online/ru-continuous-corpus-20261027`：原文件、WAV、下载账本、冻结 Manifest、历史排除表和来源缓存。
- `build/multilingual-online/ru-continuous-baseline-20261027`：56 次原始事件、片段 WAV、结果与初版分析，不覆盖。
- `build/multilingual-online/ru-continuous-review-20261027`：无推理 v2 汇总、审阅表与英中兼容结果。
- [版本化证据目录](evidence/v0.5.3-ru-continuous-2026-10-27/)：56 份原始结果、gzip 原始事件、Manifest、汇总、人工表、验证结果和所有本地产物哈希索引。音频和临时 URL 缓存留在本地，不加入 Git。

初版采集器按捕获字典顺序汇总并未单列应用语言门；**本报告仅使用 v2 事件顺序和分阶段计数**，未重跑模型。原始 v1 数据保留。采集时入口/metrics 源码在 `collector-sources` 保存，SHA 与原计划一致；之后仅补强冻结 Manifest/未知说话人认证保护，不改变本轮已收集的推理配置，v2 实现另有源码指纹。

实际命令（在上述 worktree 执行）：

```powershell
# 已执行的获取命令；不要为重评旧版本再下载或覆盖其冻结目录
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/prepare_ru_continuous_corpus.py --output build/multilingual-online/ru-continuous-corpus-20261027 --download

# 已执行的 56 次基线；重评时必须使用新的 --output，模型与 Manifest 保持不变
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/run_ru_continuous_baseline.py --manifest build/multilingual-online/ru-continuous-corpus-20261027/manifest.json --models-directory .models --output build/multilingual-online/ru-continuous-baseline-20261027

# 已执行的零推理 v2 复核；再次执行同样需要新的 --output
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/review_ru_continuous_baseline.py --manifest build/multilingual-online/ru-continuous-corpus-20261027/manifest.json --raw-results build/multilingual-online/ru-continuous-baseline-20261027 --output build/multilingual-online/ru-continuous-review-20261027

$env:QT_QPA_PLATFORM='offscreen'
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest discover -s tests -q
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py --base-ref afc33a67 --output build/multilingual-online/ru-continuous-review-20261027/en-zh-compatibility.json
```

不应将重评当成增加独立样本或借此反复选择好结果。工具拒绝旧输出目录，推理入口没有启用 locked/quarantine 的开关。若原文件丢失，重新获取也必须核对原文件/WAV/PCM 哈希；不一致则新建数据版本，不能悄悄替换。

本轮没有在线翻译、Whisper 模型下载、正式参数/过滤修改、生产操作、push、tag 或发布。待完成的人工与游戏/身份隔离证据列在下一阶段建议中。
