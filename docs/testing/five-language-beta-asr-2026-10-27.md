# A. v0.5.3 五语言 ASR 验收（2026-10-27）

**本轮完成技术基线，不提供未经人工签收的语义正确率。** [20 方向在线结果](five-language-beta-matrix-2026-10-27.md) · [阻断问题](five-language-beta-blockers-2026-10-27.md) · [发布方案](five-language-beta-release-2026-10-27.md)。

## 范围与来源

分支 `codex/multilingual-online-053`，采集起点 `1d187daa`，既有运行时参数基准 `645c6ace`。本轮仅修方向白名单、中文代码别名及在线方向的源语种策略归属；没有调整任何正式 ASR 参数、模型、Prompt、过滤阈值、OPUS 规则或 63 字段 Telemetry。

新取得 60 个真人语音文件，每语种 12 个：中文 89.34s、英语 107.06s、日语 129.00s、韩语 111.78s、俄语 126.24s。日/俄各有一对同文不同录音，因此分别只有 11 条不同参考文本；不是 60 个独立语义题或 60 名已核实说话人。来源均为公开真人朗读，**不是游戏实录、多人开黑或 Galgame 场景**，强噪声/重叠/快速游戏短报点覆盖不足。没有将独立语句拼成连续自然发言。

来源为 [Google/FLEURS 固定版本](https://huggingface.co/datasets/google/fleurs/blob/70bb2e84b976b7e960aa89f1c648e09c59f894dd/README.md)，CC-BY-4.0，署名 FLEURS / Alexis Conneau 等 / Google / 来源贡献者。参考文本使用供应方原文，本项目本轮未人工核对，语义及说话人标注均 pending。中文 locale `cmn_hans_cn`，只验普通话，不扩展汉语方言。其他 locale 为 `en_us/ja_jp/ko_kr/ru_ru`，不作为运行时语言代码使用。

25 个新负样本来自 MUSAN FreeSound noise 0012–0036，按[该子集 Public Domain 来源声明](https://huggingface.co/datasets/corypaik/musan/blob/76f9882cfa4475efe11508ac9aa32722f84ca5b7/licenses/noise/free-sound/LICENSE)使用，署名 MUSAN 作者及源贡献者，每个完整源文件取开头最多 8s。只有供应方 noise 标签，人工确认无可懂语音仍 pending；音乐数据服务返回错误，**没有补成“音乐已验收”**。25 条按固定顺序分配每源语言 5 条，日/韩/俄分别对同 5 条测两种策略；不是每语言测完全部 25 条。

历史原文件名、原文件/WAV/PCM SHA256 排除以前 FLEURS、MInDS-14 和旧称 holdout 的样本。这里只证明已扫描项目证据中未使用这些具体录音，不证明模型训练未见或独立说话人。下载账本 96,101,661 bytes（≤100MB，包含中断前已读数据），未下载模型。完整来源、许可、参考文本、原始与转换区间、哈希见 [Manifest](evidence/v0.5.3-five-language-beta-2026-10-27/dataset-manifest.json)。

## 实际模型与策略

| 源语言 | legacy / 正式 | language_aware 候选 |
|---|---|---|
| 中文 | base，多语言；language=zh，CPU 1 thread，beam 1 | 不覆盖中文，正式配置不变 |
| 英语 | base，多语言；auto，CPU 1 thread，beam 1，纯英文开关关闭 | 不覆盖英语；原纯英文 `.en` 路径另由 48 项兼容检查保护 |
| 日语 | base / auto / 1 thread / beam 1 | base / auto / 2 threads / beam 3 |
| 韩语 | base / auto / 1 thread / beam 1 | small / auto / 2 threads / beam 1 |
| 俄语 | base / auto / 1 thread / beam 1 | base / auto / 2 threads / beam 1 |

均 CPU INT8，temperature=0，空 Prompt，condition_on_previous_text=False，Whisper VAD=False，沿用实际归一化和原过滤。正式 Fast 兼容捕获为 3s / pre-roll 300ms / idle 350ms；既有三语候选为 4.5s / 450ms / 450ms。两者是现有真实策略，不是旧实验的 3s/450ms/2threads 组合。完整生效配置和每个 work item 的快照见 `asr-plan.json` 与原始结果。

Whisper base snapshot `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`，small snapshot `536b0662742c02347bc0e980a01041f333bce120`；文件指纹随结果保存。环境 i7-13700、16 核/24 线程、约 31.75GiB RAM、Windows build 26300、Python 3.10.20、faster-whisper 1.2.1、CTranslate2 4.7.2。**未限制 CPU affinity，不是低配或游戏负载实测。**

96 个语音策略进程 + 40 个负样本策略进程，共 136 个新进程，策略 AB/BA 顺序交替，首尾各补 3s 零，无整文件热身、无重试。实际生产 Capture/Pipeline/Whisper/filter 逻辑，120ms 音频注入、处理后等待 100ms 的主循环模拟；不是物理 loopback/QTimer 或游戏。观测、保存 PCM 与 JSON 的 CPU/RSS 也包括在内。

## 按语言结果

每组 12 个源文件，以下是**待人工核验参考文本的译前文本 micro 编辑距离**；不是 1−CER 语义准确率。raw/过滤后/译前全文与每录音成绩均保留。单段时延包括返回后被过滤的 ASR，识别前丢弃另计，没有伪造其推理时间。

| 源语言 / 策略 | CER | WER | ASR P50 / P95 秒 | CPU 秒/音频分钟 | 峰值采样 RSS MiB | ASR队列 P95 ms | 实测检测语言不同于配置源语的片段 |
|---|---:|---:|---:|---:|---:|---:|---:|
| zh / formal | 45.40% | — | 0.869 / 0.901 | 15.00 | 342.08 | 0.58 | 0 |
| en / formal | 51.39% | 56.23% | 1.588 / 1.622 | 30.50 | 342.59 | 0.31 | 0 |
| ja / legacy | 39.92% | — | 1.614 / 1.669 | 35.85 | 343.24 | 0.76 | 11 |
| ja / language_aware | 39.12% | — | 0.975 / 1.075 | 43.90 | 343.61 | 0.60 | 9 |
| ko / legacy | 24.11% | 46.48% | 1.628 / 1.680 | 24.91 | 342.25 | 58.05 | 1 |
| ko / language_aware | 13.37% | 33.10% | 3.101 / 3.165 | 71.61 | 728.30 | 667.95 | 1 |
| ru / legacy | 26.55% | 47.53% | 1.658 / 1.694 | 27.02 | 342.30 | 165.04 | 1 |
| ru / language_aware | 16.42% | 41.26% | 0.996 / 1.027 | 31.87 | 343.89 | 0.68 | 3 |

中文是强制 language=zh，返回 zh 不能作为独立语言检测正确证据。其他语言的 mismatch 数含弱/无声片段，不能直接计算整语句检测准确率。实体、数字、否定、关系和句尾完整率均待人工验收，不能由自动词面匹配生成真值。

CER：NFKC + casefold + Unicode 字母数字；中文繁简不折叠，日文异体/表记差异也计字符误差。中文出现繁体识别输出，不能把所有 CER 当作语义错误。日/中文没有人工分词或可信词分词器，**WER 留空**，另存字符/kana/其他字母数字单位 UER；不拿整句当一个英文词。韩文 WER 是 eojeol，俄文保留西里尔字母，英语保留字面词/数字形式（数词与阿拉伯数字不同可能产生表面误差）。不能与旧报告不同语料、不同归一化的分数直接做质量退化归因。

对齐使用每进程一个完整源文件、真实 whisper_end 顺序；没有逐段人工词/帧真值，不给流式片段乱配整句参考。重叠/重复/重排会禁止该录音评分；本轮 136 份结果全部通过此结构检查。捕获未覆盖区间单独保存，不自动认定语音漏帧。韩语候选有 1 次正式短段合并，原父片段与合并片段均保留。

## 切段与过滤

| 源 / 策略 | 捕获 | Whisper 返回 | 识别前丢弃（预算） | ASR后过滤 | 译前语言门拒绝 | 译前非空片段 |
|---|---:|---:|---:|---:|---:|---:|
| zh / formal | 35 | 25 | 10（5） | 4 | 0 | 21 |
| en / formal | 68 | 34 | 34（21） | 4 | 0 | 30 |
| ja / legacy | 60 | 46 | 14（13） | 13 | 0 | 33 |
| ja / language_aware | 49 | 41 | 8（6） | 14 | 0 | 27 |
| ko / legacy | 45 | 28 | 17（9） | 3 | 0 | 25 |
| ko / language_aware | 36 | 21 | 14（6） | 1 | 0 | 20 |
| ru / legacy | 55 | 34 | 21（16） | 1 | 1 | 32 |
| ru / language_aware | 40 | 30 | 10（7） | 1 | 1 | 28 |

全部进程正常排空，无原音频队列丢块、无未完成 ASR。是否丢弃有效语义仍需人工帧标注，不能把预算拒绝数全部叫误杀。日语 `beta-ja-1731-10203675650837159328` 两策略均整录音译前为空：低置信度韩语/日语 raw、empty_asr、预算丢弃共同出现；候选尾段 raw `アリマッセン` 被弱候选阈值拒绝，**尚不能靠来源全文断定该段声学内容被正确识别**。不放宽阈值凑通过。

## 负样本（每源语言 5 条）

| 源 / 策略 | raw 非空录音 | 译前非空录音 | ASR P95 秒 | CPU 秒/音频分钟 |
|---|---:|---:|---:|---:|
| zh / formal | 3/5 | 2/5 | 1.698 | 22.73 |
| en / formal | 3/5 | 0/5 | 2.152 | 39.86 |
| ja / legacy | 2/5 | 1/5 | 2.199 | 41.29 |
| ja / language_aware | 5/5 | 0/5 | 2.196 | 50.80 |
| ko / legacy | 3/5 | 0/5 | 2.759 | 43.24 |
| ko / language_aware | 5/5 | 0/5 | 5.127 | 132.41 |
| ru / legacy | 3/5 | 0/5 | 2.806 | 39.86 |
| ru / language_aware | 3/5 | 0/5 | 1.707 | 38.47 |

这里是供应方标为 noise 的输入，**疑似误触发，不是人工证实的假阳性率**；本轮没有把负样本发给在线 API。不同源语言分配不同 5 条，不可直接比较跨语言误触发率。有效短语音误杀和噪声漏放两侧都必须复核，不能只改召回阈值。

本轮没有按平均 CER 选择新发布默认，也未实施日/韩/俄 ASR 参数修复。日韩俄两策略同时改动的变量已快照，不能从平均值归因某一个参数。468 项片段人工材料见 `human-asr-segment-review.json`；[完整 ASR 汇总](evidence/v0.5.3-five-language-beta-2026-10-27/asr-summary.json)。
