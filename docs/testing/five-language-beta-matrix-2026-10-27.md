# B. 五语言 20 方向翻译与原生字幕（2026-10-27）

**20 个方向均已真实调用固定 SiliconFlow Hunyuan-MT-7B，且均至少生成过一次非空原生 Qt 字幕；这不是 20 方向质量验收通过。** [ASR结果](five-language-beta-asr-2026-10-27.md) · [阻断问题](five-language-beta-blockers-2026-10-27.md) · [发布方案](five-language-beta-release-2026-10-27.md)。

## 代码核查与最小修复

采集起点 `1d187daa` 实际只允许 14 个方向：日↔韩、日↔俄、韩↔俄共 6 个在客户端请求前拒绝；三语候选 ASR 也只在目标 en/zh 时生效。已修为固定五语的 20 个不同源/目标组合，并让源语种策略不依赖目标为中文。旧 14 方向所有生效 Audio/Whisper 配置逐项比较无差异。

核心代码位置（采集/交付源码指纹在证据中）：

- `voxgo/languages.py:25 normalize_language_code`：`zh_CN/zh-CN`→`zh`；`:31 normalize_language_flow` 保留显式非法方向而非猜英语；`:44 translation_direction_error`：在线 20，OPUS 离线仍只有 en↔zh；`:53 whisper_model_error` 与实际模型 multilingual 能力检查共同阻止非英语用 `.en`。
- `voxgo/ui/overlay_window.py:628 _sync_language_controls`、`:665 _language_combo_changed`、`:680 _apply_language_flow`：每个源 4 个目标、交换及设置回调。换源时默认目标仍为旧默认 en/zh，**是默认选项，不是强制翻译成中文**；明确选定的非中文目标被保留并实际发出。
- `voxgo/config/loader.py:605 sync_language_flow`：翻译源/目标与 Whisper 强制语言分开；中文用 zh，多语言模型；英语普通模式 auto；日/韩/俄 auto，自动检测用于过滤，不自动改变用户目标或 Provider。旧 yue 等兼容别名不构成新增方言验收。
- `voxgo/asr/language_profiles.py:23 effective_speech_config`：只有日/韩/俄、在线、Fast、非 Ultra Low 且候选开关启用时覆盖；en/zh 不变。共享开关仍同时控制三语，没有本轮新增每语默认策略。
- `voxgo/translation/google.py`：内部 zh→`zh-CN`，其他 en/ja/ko/ru 同码；v2 单请求直接传 source/target。`openai_compatible.py` + `prompt.py.translation_system_prompt`：直接写真实源/目标，只发一次请求；中英旧 SYSTEM_PROMPT 完全不改。中文提示词文字不代表客户端中文中转。
- `voxgo/app.py:375 _handle_language_flow_changed`、`:507 _handle_transcript_ready`、`:582 _handle_translation_ready`、`translation/runtime.py:390 _is_stale_language_flow`：版本快照、清理待处理语音/上下文、前后检查旧结果，防止错语言字幕。已经在 HTTP 中的任务不保证物理取消，可能继续占用串行槽；不能把单元测试当真实热切换/游戏验收。
- `voxgo/translation/client.py:107 translate_result_with_config`：保留配置快照，非法方向先拒绝；在线/本地分支明确，无收费或其他语言回退。旧 `validate_multilingual_live.audio_run` 只测三语→中文，**本轮未用它冒充 20 方向**，而是复用观察器通用入口。

Whisper 使用 transcribe 路径，不先翻译成英语。客户端未发现隐式中文/英文中转。Google [官方语言表](https://docs.cloud.google.com/translate/docs/languages)声明支持这些语言，OpenAI-compatible 本身不保证任意模型能力。本轮只有固定 SF 模型真实验收，Google 及其他兼容模型均**未真实验收**。

## 20 方向支持矩阵

F=现有正式 Fast，L/A=兼容/候选源语策略（详情见 A）。SF=本轮真实硅基流动；G=Google 仅本地 HTTP 契约。每条在线均需用户自配 Key/支持该语言的模型，不自动切服务；只有英中可选本地 OPUS。

| source | target | ASR配置 | Provider证据 | 语言路由 | 配置限制 | 1d187daa → 当前 |
|---|---|---|---|---|---|---|
| en | ja | F base/auto | SF真实；G契约 | en → ja，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| en | ko | F base/auto | SF真实；G契约 | en → ko，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| en | ru | F base/auto | SF真实；G契约 | en → ru，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| en | zh | F base/auto | SF真实；G契约 | en → zh-CN，单跳 | 可选英中OPUS；在线需Key | 路由允许 → 技术连通，质量未签收 |
| ja | en | L/A base/auto | SF真实；G契约 | ja → en，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| ja | ko | L/A base/auto | SF真实；G契约 | ja → ko，单跳 | 仅在线、自配Key；OPUS拒绝 | 拒绝 → 技术连通，质量未签收 |
| ja | ru | L/A base/auto | SF真实；G契约 | ja → ru，单跳 | 仅在线、自配Key；OPUS拒绝 | 拒绝 → 技术连通，质量未签收 |
| ja | zh | L/A base/auto | SF真实；G契约 | ja → zh-CN，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| ko | en | L base / A small，auto | SF真实；G契约 | ko → en，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| ko | ja | L base / A small，auto | SF真实；G契约 | ko → ja，单跳 | 仅在线、自配Key；OPUS拒绝 | 拒绝 → 技术连通，质量未签收 |
| ko | ru | L base / A small，auto | SF真实；G契约 | ko → ru，单跳 | 仅在线、自配Key；OPUS拒绝 | 拒绝 → 技术连通，质量未签收 |
| ko | zh | L base / A small，auto | SF真实；G契约 | ko → zh-CN，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| ru | en | L/A base/auto | SF真实；G契约 | ru → en，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| ru | ja | L/A base/auto | SF真实；G契约 | ru → ja，单跳 | 仅在线、自配Key；OPUS拒绝 | 拒绝 → 技术连通，质量未签收 |
| ru | ko | L/A base/auto | SF真实；G契约 | ru → ko，单跳 | 仅在线、自配Key；OPUS拒绝 | 拒绝 → 技术连通，质量未签收 |
| ru | zh | L/A base/auto | SF真实；G契约 | ru → zh-CN，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| zh | en | F base/zh | SF真实；G契约 | zh-CN → en，单跳 | 可选英中OPUS；在线需Key | 路由允许 → 技术连通，质量未签收 |
| zh | ja | F base/zh | SF真实；G契约 | zh-CN → ja，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| zh | ko | F base/zh | SF真实；G契约 | zh-CN → ko，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |
| zh | ru | F base/zh | SF真实；G契约 | zh-CN → ru，单跳 | 仅在线、自配Key；OPUS拒绝 | 路由允许 → 技术连通，质量未签收 |

## 真实请求与 20 方向结果

授权计划：60 次自编文本（短报点/连续条件/数字否定角色）、60 次原语音参考全文、预计 136 次实际 ASR 片段；用户明确授权上限 300。实际 **255 次 = 60 + 60 + 135**，无重试/补跑、无换模型、无重定向，45 次余量未使用。实际捕获切段随调度产生 1 次数量差异，原 PCM/每段边界均保存，没有合并字幕来凑次数。

固定 `https://api.siliconflow.cn/v1/chat/completions`、`tencent/Hunyuan-MT-7B`，temperature=0、timeout=12s、max_tokens=80（既有配置）、context=0、并发=1（本机既有值）；基准关闭本地短语缓存以测真实 Provider，未修改用户设置。并发 1 的测量不能外推为程序所有并发设置的性能。

按[官方价目页](https://siliconflow.cn/pricing)输入/输出免费估算 **¥0**，未读取账户账单。成功响应回传 token 合计 74,922；超时未回传 usage，不把它伪装为全部精确消耗。请求 ledger 保存全部尝试、Prompt、原文、目标、状态、失败与队列计时；服务端权重具体 revision 未采集，不能保证未来相同输出。

| 方向 | 自编纯文本非空200 | 标准原文非空200（length截断） | 流式HTTP非空200/尝试 | 非空字幕用例/计划 | 末PCM→Qt P95秒 | 目标脚本异常疑点 | 发布状态 |
|---|---:|---:|---:|---:|---:|---:|---|
| en→ja | 3/3 | 3/3（0） | 9/9 | 3/3 | 2.92 | 0 | 未签收；见阻断项 |
| en→ko | 3/3 | 3/3（1） | 12/12 | 3/3 | 3.10 | 0 | 未签收；见阻断项 |
| en→ru | 3/3 | 3/3（1） | 11/11 | 3/3 | 3.40 | 0 | 未签收；见阻断项 |
| en→zh | 3/3 | 3/3（0） | 11/11 | 3/3 | 12.72 | 0 | 未签收；见阻断项 |
| ja→en | 3/3 | 3/3（0） | 4/4 | 2/3 | 17.56 | 0 | 未签收；见阻断项 |
| ja→ko | 3/3 | 3/3（0） | 4/4 | 2/3 | 10.30 | 0 | 未签收；见阻断项 |
| ja→ru | 3/3 | 3/3（0） | 2/4 | 1/3 | 2.41 | 0 | 未签收；见阻断项 |
| ja→zh | 3/3 | 3/3（0） | 2/4 | 1/3 | 1.77 | 0 | 未签收；见阻断项 |
| ko→en | 3/3 | 3/3（0） | 7/7 | 3/3 | 6.55 | 0 | 未签收；见阻断项 |
| ko→ja | 3/3 | 3/3（0） | 7/7 | 3/3 | 4.82 | 0 | 未签收；见阻断项 |
| ko→ru | 3/3 | 3/3（1） | 7/7 | 3/3 | 4.77 | 0 | 未签收；见阻断项 |
| ko→zh | 3/3 | 3/3（0） | 7/7 | 3/3 | 4.39 | 0 | 未签收；见阻断项 |
| ru→en | 3/3 | 3/3（0） | 5/5 | 3/3 | 1.90 | 0 | 未签收；见阻断项 |
| ru→ja | 3/3 | 3/3（0） | 5/5 | 3/3 | 2.00 | 0 | 未签收；见阻断项 |
| ru→ko | 3/3 | 3/3（1） | 5/5 | 3/3 | 2.40 | 0 | 未签收；见阻断项 |
| ru→zh | 3/3 | 3/3（0） | 5/5 | 3/3 | 1.87 | 0 | 未签收；见阻断项 |
| zh→en | 3/3 | 3/3（0） | 7/7 | 3/3 | 1.61 | 0 | 未签收；见阻断项 |
| zh→ja | 3/3 | 3/3（0） | 7/7 | 3/3 | 1.85 | 0 | 未签收；见阻断项 |
| zh→ko | 3/3 | 3/3（0） | 7/7 | 3/3 | 1.78 | 0 | 未签收；见阻断项 |
| zh→ru | 3/3 | 3/3（0） | 7/7 | 3/3 | 1.87 | 0 | 未签收；见阻断项 |

每方向 3 条不同录音，但四个目标复用同一源语的 3 条，总计 **15 个独立录音、60 个方向播放**。不能算 60 条独立语音或可靠长期方向准确率。纯文本 60 条全部 HTTP 200、finish=stop，但存在关键含义错译；参考全文 60 条全部 HTTP 200，其中 4 条 finish_reason=length。

| 计数层级 | 实际结果 |
|---|---:|
| 计划/实际执行语音方向用例 | 60 / 60 |
| Whisper 返回 / 非空归一化输出 | 165 / 153 片段（不是语义识别正确数） |
| 识别前丢弃 / ASR后过滤 / 应用语言门拒绝 | 70 / 26 / 4 |
| 过滤后保留 / 实际送翻译 | 139 / 135 片段 |
| 流式 HTTP 200 / 超时 / 未完成 | 131 / 4 / 0 |
| 最终非空可复制字幕 | 131 片段，54/60 用例至少一条（90%） |
| 全批 HTTP 完整200 / 尝试 | 251/255（98.43%） |
| 人工确认正确目标语、可理解字幕、关键语义正确率 | 全部未完成，不能填 100% 或 0% |

全批 HTTP 成功达到本次建议 95% 的点估计，不等同长期稳定性，也不等于字幕 90% 或人工 85%。自动脚本检查 0 个缺失目标脚本疑点，但这不是人工目标语言正确率；日文纯汉字还会被标 ambiguous。内容 length 截断另计，不能由 HTTP 200 宣称完整。

## 完整链路时延与失败

全批客户端调用（含 API 队列与失败）P50/P95 **0.788/5.385s**；扣除实测 semaphore 等待后的 HTTP 阶段估计 **0.763/3.160s**。后者含本地开销、网络和服务端，不能拆成纯服务商计算时间。API 槽排队最大 **9.064s**；例如日→英一段总调用 17.458s，其中排队 5.570s、Provider成功返回耗时 11.884s。不能把这个长尾归因于 Whisper。

有非空字幕的 131 片段，“末 PCM 帧→原生 Qt item 更新”P50/P95 **2.427/9.781s**。按源语合并四目标：中 1.531/1.882s、英 2.602/11.857s、日 5.225/14.686s、韩 4.246/4.843s、俄 1.792/2.195s。**仅是文件流代理计时**：不包括无字幕用例的成功端点，不是人工语音结束、物理屏幕 scanout 或游戏延迟。4 条 ASR 无输入用例和 2 条全部 HTTP 超时用例明确单列，未用成功片段隐藏失败。

四次超时均发生在 HTTP 阶段：日→俄 `beta-ja-1980-10300959819649327821` 两次，日→中 `beta-ja-1828-10020345318418093976` 两次；12s配置实际触发约12–13s，另有槽等待。无法进一步判断线路、连接还是服务商内部排队，没有归咎 ASR，也没有补跑。

日语 `beta-ja-1731-10203675650837159328` 四目标均无译前输入、未发 API；不是四条独立坏录音。其它目标至少有过真实字幕，只证明链路可执行，不证明含义完整。

原生模式为 `QApplication.platformName=windows`，本地协议 20/20 + 60 个真实在线 QWidget 实测，全部排空、进程正常退出；截图是所属窗口内容。没有用 offscreen 代替 native。**仍未完成 Full EXE 完整 GUI 手验、物理 loopback、长时间单客户端切换、真实游戏/FPS**。60 个新进程不等于持续运行稳定性。

## A/B 对照与人工材料

[配对材料](evidence/v0.5.3-five-language-beta-2026-10-27/paired-human-review.json)含每方向来源/标准原文/A译文/实际PCM边界/raw与过滤后ASR/B译文/原生字幕/时延/待填问题等级；[全部汇总](evidence/v0.5.3-five-language-beta-2026-10-27/online-summary.json)。A 是参考全文，B 是真实流式片段，**上下文不同且没有人工逐词帧对齐**，不可把全部 A/B 差异都算 Whisper 错误。自编纯文本绕过 ASR，能直接暴露 Provider+当前 Prompt 组合的翻译问题；B raw 已错只证明错误先于翻译，Capture 与 Whisper 的因果仍需听音。

全部来源与人工标注 pending；AI 辅助只记疑点，不给人工准确率。[AI 阅读记录](evidence/v0.5.3-five-language-beta-2026-10-27/ai-text-review.json)覆盖全部 60 自编输出，具体关键例见 C。本轮实际 API 已结束，不再使用剩余配额补跑。
