# v0.5.3 阻断项20次真实在线复测（2026-10-28）

**已完成用户新授权的20次，未重试、未补跑。截断防护通过真实Provider→原生Qt复测；四个旧语义问题仍复现，完整五语Beta仍不具备发布结论。** 本批只执行[已批准的小规模文本计划](evidence/v0.5.3-beta-blockers-2026-10-28/next-online-plan.json)，没有ASR、私人音频、Full EXE、生产遥测、迁移/部署或发布操作。

执行分支 `codex/multilingual-online-053`，执行时HEAD `82a3e5ec`，运行时修复 `f7d2c35f`。正式`voxgo/`相对该修复提交无变化；新增的执行器只用于本地评测，不进入Full包。旧255次请求账本SHA256仍为 `c57726c844742cbc84e80a649a6548bec4fa72b17b80b09de4de075dd6340155`。原计划保持原样，用户“确认执行”记录在独立授权文件；旧300次授权未复用。

## 请求、字幕与延迟

固定本机既有SiliconFlow `tencent/Hunyuan-MT-7B`，直接源→目标；max_tokens=80、temperature=0、context=0、并发1、timeout=12s，禁用实验短语缓存。实际POST前校验计划、源/目标/原文、固定模型、Prompt、参数和HTTPS路径，每次预留账本计数；禁止重定向、重试、换模型或Provider。

| 指标 | 实际结果 |
|---|---|
| 计划 / 硬上限 / 实际尝试 | 20 / 20 / **20** |
| 完整HTTP 200 JSON | **20/20**（传输成功，不等于内容完整或语义正确） |
| `finish_reason=stop` | **16**，产生16条可复制原生字幕 |
| `finish_reason=length` | **4**，全部显示不可复制的`[翻译不完整]`提示，partial不作为正常字幕 |
| 超时 / 取消 / 未完成 / 重试 | **0 / 0 / 0 / 0** |
| 模型/源目标/Prompt/预算与计划一致 | 全部20条；无静默回退或中转 |
| API调用耗时 P50/P95 | **1.010 / 2.613s**（全部20条，包含length；含客户端等槽与HTTP） |
| 文本提交→Qt条目更新 P50/P95 | **1.023 / 2.631s**（含4条错误提示；不是语音结束/显示scanout/游戏延迟） |
| Provider报告usage | prompt **5,847**、completion **707**、total **6,554** tokens |
| 用户原配置 / 资源清理 | 前后SHA256相同；Runtime关闭、线程退出，未初始化生产遥测 |
| 人工目标语言/可理解率/语义正确率 | **未验收**，不由AI或非空字幕生成数值 |

本批为串行文本用例，没有制造实时队列积压或切语种取消，不用这些时延证明上轮9.78s语音字幕长尾已经修好。旧请求取消另有零外网回环、后台Runtime和fallback loop测试；本轮没有增加任何实时语音验收。

| 方向 | 请求 | stop / length | 正常字幕 / 错误提示 | 质量状态 |
|---|---:|---:|---:|---|
| zh→en | 4 | 4 / 0 | 4 / 0 | 旧地下层误译复现；新例/回归待人工 |
| ru→ja | 2 | 2 / 0 | 2 / 0 | 旧行动时序疑点复现；新句待人工 |
| ko→zh | 2 | 2 / 0 | 2 / 0 | 旧治疗角色→房间复现；新句待人工 |
| zh→ru | 2 | 2 / 0 | 2 / 0 | 旧明确数量遗漏复现；新句待人工 |
| en→ko | 2 | 1 / 1 | 1 / 1 | 新长句截断被拦，短句待人工 |
| en→ru | 2 | 1 / 1 | 1 / 1 | 新长句截断被拦，短句待人工 |
| ko→ru | 2 | 1 / 1 | 1 / 1 | 新长句截断被拦，短句待人工 |
| ru→ko | 2 | 1 / 1 | 1 / 1 | 新长句截断被拦，短句待人工 |
| en→zh | 2 | 2 / 0 | 2 / 0 | 新英中回归未见明显关键词面差异，待人工 |

只有这9个受影响/回归方向本轮有真实调用，其余11方向未重测；保留上轮技术连通证据，不宣称重新验收完整20方向。

## 语义复核：四个旧例与四个新句

以下是AI辅助词面/含义审阅，**不是双语人工签收**。四个旧锚点输出逐字与上一批一致；软件本轮没有改Prompt或模型，因此不能把新句表现归因于运行时修复。

| 用例 | 关键原文 | 本次实际输出 | AI辅助判断 |
|---|---|---|---|
| semantic-anchor-1，zh→en | 地下一层 | `he is on the ground floor` | 地下变地面楼层，旧问题复现 |
| semantic-new-1，zh→en | 地下二层有1队友，地面一层无人 | `a teammate on the second underground floor, and no one on the first floor above ground` | 地下/地面与人数有表达，楼层习惯待人工 |
| semantic-anchor-2，ru→ja | `Когда я досчитаю до трёх, отступаем вместе.` | `私が「三」と数えるまで、一緒に後退してください。` | “数到3时撤退”仍疑似变成“直到数到3前撤退” |
| semantic-new-2，ru→ja | 守位直到数到4，然后撤退 | `私が「4」まで数える間、その位置を守ってください。その後で撤退してください。` | 守位/之后撤退顺序有表达 |
| semantic-anchor-3，ko→zh | `힐러는…` | `治疗室不在二楼…` | 角色变房间，旧问题复现 |
| semantic-new-3，ko→zh | 2名治疗角色在地下2层；治疗室在1层 | `两名治疗师在地下二楼，治疗室在一楼。` | 人物/房间、人数和楼层分别有表达 |
| semantic-anchor-4，zh→ru | 左边两个人，别开枪 | `Люди слева, не стреляйте.` | 数量2仍未表达；源句命令受事歧义另记 |
| semantic-new-4，zh→ru | 左侧3名敌人，先别开枪，等信号 | `Слева трое врагов. Сначала не стреляйте, подождите моего сигнала.` | 明确敌人/3/等待信号有表达 |

其它4个短句控制和4个新英中回归，AI未见相同类型的明显关键词面遗漏；仍需人工确认自然性、语境和目标语言，不给“12/12正确率”。全部20条的完整源文、raw、最终字幕、失败分类、usage、计时及独立人工栏见[AI辅助/人工待审材料](evidence/v0.5.3-beta-blockers-online-2026-10-28/ai-assisted-review.json)和[原始结果](evidence/v0.5.3-beta-blockers-online-2026-10-28/results.json)。

## 截断修复的真实验证

四个新长句分别为en→ko/en→ru/ko→ru/ru→ko，均返回显式`length`。Provider报告completion tokens为 **78、80、80、80**，所以不能只用`usage==max_tokens`判断截断；正式代码依明确的finish_reason拦截，本次4/4均有效。

原始partial保存供本地人工检查，但屏幕只显示`[翻译不完整] 服务商达到输出上限，未显示截断译文。请检查 max_tokens 设置。`，copyable=False；没有自动扩大预算或重发。已有`other`失败类别沿用，未扩63字段。上下文配置为0，代码在length分支返回而不存上下文；此前本地测试也覆盖非零上下文不复用partial。

示例截图（源码原生Qt组件，不是Full EXE手验）：[en→ko截断提示](evidence/v0.5.3-beta-blockers-online-2026-10-28/screenshots/length-long-1.png)、[ru→ja新对照句](evidence/v0.5.3-beta-blockers-online-2026-10-28/screenshots/semantic-new-2.png)。截断样本中也可能有错误的prefix，例如en→ru的“红灯熄灭”前缀疑似译“亮起”，该partial未作为字幕，不对全文给质量通过结论。

修复的是“把不完整输出当成完整字幕”的问题，**不是让80 token能够完整翻译这些长段落**。4/20刻意包含长边界用例，不能把16/20正常字幕比例推算成日常成功率或人工可理解率。完整长对白仍需独立预算/模型策略验收，不能直接全局提高上限。

## 授权、价格、代码与复现边界

- 当前[官方价格页](https://siliconflow.cn/pricing)已实际HTTPS抓取HTTP200并确认该模型输入/输出免费，预估费用¥0；不是账户账单核销。来源、抓取UTC时间、页面SHA256与模型行在[price.json](evidence/v0.5.3-beta-blockers-online-2026-10-28/price.json)。
- 一次性授权绑定计划SHA256 `bfa0f678548d21fd2bf2c63c139ceddcd220447523c68909b2f9f19d422aa248`及独立目录。已消费，不能换目录复用；不能用本轮授权再补跑失败题。
- 配置只读、原设置SHA256前后均为 `73df2586a0781971ea9f391abdab9dbc2e33401ef87d5db08e70314ce776ad5e`。API Key只在进程内用于授权，不存配置副本/日志/报告/截图。对Provider日志关闭落盘，保存字段按Key精确去敏。
- 仅新增`scripts/run_beta_blocker_online.py`及其3项测试，复用旧`AttemptBudget/MeasuredClient/claim_run`，原20方向、模型、ASR、Prompt、OPUS和Telemetry源码均未改。没有下载模型/依赖。
- 本轮 **18项零外网预检通过**：新执行器3项、既有授权/HTTP计数7项、发布阻断修复8项。包括精确达到20时完成、限流停止、partial不显示、正常路线、取消与关闭。预检的回环HTTP结果明确标为fixture，不计入真实20次。
- 本轮没有再跑客户端全量/API全量；此前630/70及英中48配置一致仍是原运行时的验证基线。新增评测工具不进入发布包。

实际已执行命令（当前授权已消费，不要重发）：

```powershell
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest tests.test_beta_blocker_online tests.test_five_language_online_acceptance tests.test_beta_release_blockers -q
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/run_beta_blocker_online.py --run-live --plan docs/testing/evidence/v0.5.3-beta-blockers-2026-10-28/next-online-plan.json --approval build/beta-blockers-online-20261028-20.authorization.json --settings E:/my/my/game_voice_translator/user_settings.json --output build/beta-blockers-online-20261028-20
```

[独立证据目录](evidence/v0.5.3-beta-blockers-online-2026-10-28/)含20次账本、完整结果/partial、20张原生截图、授权及消费标记、实时价格证明、清理与设置校验、预检日志、执行时脚本字节副本和待人工表。本地原始目录`build/beta-blockers-online-20261028-20`保留，没有覆盖旧结果。

下一步仍是双语人工裁定关键语义与日语漏句，以及Full/真实游戏验收；如另开通用Prompt A/B，必须先列新计划、隔离正式英中行为并另行授权。**本轮到20次停止，不继续调参、请求或发布。**
