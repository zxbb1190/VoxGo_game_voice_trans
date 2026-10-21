# 多语言在线翻译独立验收材料

本文件记录语料、评审和测量方法。实现通过协议测试不等于某个语言已经达到发布要求；实际执行结果应同时记录在本轮 RC 记录中。人工质量验收、真实游戏场景及低配置 Windows 真机验收目前均未完成。

## 固定语料与独立样本

语料为 [cases.json](../../tests/assets/multilingual_online/cases.json)，96 条新编写测试提示，与原日语英语中转、英中离线调参语料独立。它们不是游戏录音转写，也没有母语自然度或参考译意的人工认证。所有语言的人工状态均为 `pending`。数字、方向、否定、条件、时间、术语及信息完整性在每个方向的 dev 和 holdout 中均有覆盖。

| 方向 | dev | holdout | 场景 |
| --- | ---: | ---: | --- |
| en → zh | 6 | 6 | 开黑短句、配音、剧情 |
| zh → en | 6 | 6 | 开黑短句、配音、剧情 |
| ja → zh | 10 | 10 | 开黑短句、配音、剧情 |
| ko → zh | 10 | 10 | 紧急报点、战术短句 |
| ru → zh | 10 | 10 | 紧急报点、战术短句 |
| zh → ja | 6 | 6 | 补充方向：开黑短句、配音、剧情 |

在开发前固定 split，不根据输出移动样本。dev 可用于定位机制问题；holdout 留作改动后的独立回归。不得以某条英文、日文或中文原句为键加入运行时答案，也不得用 holdout 答案选择 Prompt、术语规则或模型参数。若开发中已查看某个 holdout 的结果并据此调参，该样本应标记污染，下一轮新增独立验收集；不把它重新算作独立证据。

生成评审表（默认不请求网络、不读取用户设置或环境中的 API Key）：

```powershell
.\.venv-win\Scripts\python.exe scripts/evaluate_multilingual_online.py --mode prep
.\.venv-win\Scripts\python.exe scripts/evaluate_multilingual_online.py --mode mock --provider google --output build/multilingual-online/mock-google
.\.venv-win\Scripts\python.exe scripts/evaluate_multilingual_online.py --mode mock --provider openai_compatible --output build/multilingual-online/mock-openai
.\.venv-win\Scripts\python.exe -m unittest tests.test_multilingual_online_corpus -q
```

工具输出 `review.jsonl`、带 UTF-8 BOM 的 `review.csv` 和 `summary.json`。mock 经现有 `GameTranslator` 和两个正式 Provider 的请求/响应路径，禁用本地短语缓存，使用内存 transport 捕获公开请求载荷；不会建立 socket。mock 输出只写入 `mock_output`，实际 `translation_output`、质量和 ASR / 翻译 / 端到端延迟均留空（JSON `null`），不会生成虚假的 0 毫秒或正确率。prep 不导入实际模型。工具没有 live 模式，本轮真实在线调用由主验收流程统一记录授权、请求预算及消费，不能把 mock 结果混入。

## 人工质量表的填写

评审人应能独立核对源语言和目标语言。先审校原句自然度与 `reference_meaning` / `key_meanings`，有歧义时保留问题并修订下一版语料，不能仅凭目标参考译文判错。对真实输出记录：

- `translation_output` 为原文直接到目标语言的输出，不存在英文中转列；保留 Provider / 模型、版本、请求参数和原始响应的独立记录。
- `human_key_meaning_verdict` 填 `pass` / `fail` / `unjudgeable`；数字、单位、方向、否定、条件、目标对象及每个必要句意都正确才能通过。语气自然但关键含义错误仍为失败。
- `human_error_categories` 记录 `number`、`time`、`direction`、`negation`、`condition`、`terminology`、`completeness`，可多选；`human_notes` 写清丢失或反转的关键意义。
- `suspected_errors` 只列待核实疑点。AI 可以辅助发现疑点，不可代替人工填写验收通过。填写 `reviewer`、`reviewed_at` 及复核意见后才改变 `human_review`。
- 分别保留 `asr_transcript` / `asr_error_notes`：原转写直接翻译错误属于翻译阶段；ASR 先识别错、翻译忠实于错误转写时优先归因 ASR。同时保留从标准转写翻译的对照，避免混合归因。

关键含义正确率 = 人工 `pass` 条数 / 人工可判定条数，同时报告 `fail`、`unjudgeable`、未评数量和评审覆盖率。未评时正确率是“未完成”，不能写 0% 或 100%；不能用部分已评结果代表全体。按方向、split 和场景分别展示。任何已知可复现的方向、数值/时间单位、否定、条件反转或重要整句遗漏应作为独立发布阻断问题处理。

## 真实语音与许可

本轮准备的最低限度公开真实语音基线采用 Google FLEURS，版本 `70bb2e84b976b7e960aa89f1c648e09c59f894dd`，许可 [CC BY 4.0，Google 数据集卡](https://huggingface.co/datasets/google/fleurs/blob/70bb2e84b976b7e960aa89f1c648e09c59f894dd/README.md)。音频是人类百科类朗读，不能代表游戏配音、剧情情绪、多人开黑、重叠说话或噪声环境。不要把 TTS、公开朗读或合成压力标为真实游戏测试。

本地忽略目录 `build/multilingual-online/audio/` 存放每种语言三段短语音（JA 复用既有缓存，KO/RU 从固定版本 test 归档有界提取）、原转写、来源与许可 URL、逐文件 SHA-256、原归档成员 SHA-256及 PCM 转换说明。只核验所使用成员，未下载完整归档，不能声称整个远端 tar 的校验已验证。音频不进入客户端打包或正式模型下载。`manifest.json` 是统一入口；`prepare_fleurs.py` 仅为本地准备记录，直接下载公开数据，不涉及在线翻译 Key 或费用。不同片段和性别元信息不等同已确认不同说话人，未验说话人身份。

日语合法授权的真实游戏配音/剧情、韩语和俄语合法授权的多人开黑录音，以及双语人工评审仍需另行补足。未找到可可靠核验许可的对话语料时保留缺口，不从商业游戏或视频随意抓音频冒充已授权样本。

## 可复现性能测量与逐语言门槛

每个方向单独记录模型版本/哈希、真实 `effective_model`（JA/KO/RU 不得为 `.en`）、源语言和检测结果、Provider / 模型及直达目标、CPU/内存、线程、GPU、音频设备/块大小、音频 SHA 和时长、客户端 SHA、请求失败与输出丢弃原因。正式 ASR 参数与 Prompt 保持原样，不为了某个样本临时调优。

使用正式 `SystemAudioCapture → SpeechPipeline → 翻译事件 → 字幕显示` 路径，先以 PCM 回放做可重现测量，再做真实声卡和游戏测试。记录单调时钟的语音起始、语音结束、切段发出、ASR 开始/完成、请求排队/发出/完成、字幕提交/实际显示时间，区分：

| 维度 | 必须记录 |
| --- | --- |
| ASR | 原转写/实际转写/检测语言、关键语义误识别、耗时、RTF、切段与候选缓冲等待 |
| 直接翻译 | 标准转写直接翻译、ASR 输出直接翻译、请求耗时、排队耗时、关键意义人工判定 |
| 端到端 | 从语音结束到真实字幕显示的 P50/P95，同时列从语音起始到显示；不能用各阶段 P95 相加 |
| 资源 | 进程树 CPU（说明每核/整机口径）、峰值 RSS、系统内存与页面文件、游戏平均 FPS/1% low/frame time，与同场景无 VoxGo 基线成对比较 |
| 压力 | i7-13700 全量与限核、固定并发及 CPU 背景负载；后台负载是否占用同核要记录。明确标注“受限 CPU 压力测试”，不能代替低配真机 |

预热和冷启动分开；同一设备至少三轮，报告有效样本数、每个样本原始延迟、P50/P95算法、失败/超时/丢弃比例及排队增长，不能只对成功快样本计时。每种语言的短句、配音/剧情（适用时）分别汇总；3 段朗读仅可发现明显故障，无法支撑稳定的 P95 或质量发布结论。实际请求在用户明确授权的 Provider、模型与费用上限内执行，超预算或无授权时保持待验。

逐语言验收均需要：方向/模型能力与显式限制回归通过；未污染 holdout 的双语人工关键语义评审；真实游戏场景 ASR 与直译质量对照；正式字幕路径及资源/游戏影响；目标低配设备验收。准确率和延迟的正式数值门槛应在查看结果前由产品确认，当前尚无已批准数值，本材料不能自行宣布达标。只要其中任何一项缺证据，该方向状态为“待验收”，不得因其他语言通过、供应商支持列表或单元测试成功而直接放行。
