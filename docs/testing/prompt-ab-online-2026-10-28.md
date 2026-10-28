# v0.5.3 通用Prompt：24次真实A/B（2026-10-28）

**24次已全部执行，未重试、未补跑；当前不建议替换正式Prompt。** 12条新句中8对输出逐字相同，4对主要为措辞/格式变化，AI辅助审阅未找到足以证明候选带来关键语义收益的证据。双语人工仍待完成，不给语义正确率或“12/12通过”结论。

执行分支`codex/multilingual-online-053`，起点`97d8bbfe`。仅新增独立实验工具、测试和本报告/证据；正式`voxgo/`、用户配置、ASR、OPUS和63字段Telemetry均未改变。没有生产操作、push、tag或发布。

## 授权与固定范围

用户明确授权“这24次Prompt A/B…硬上限24次、不重试”。复用[冻结的12句计划](evidence/v0.5.3-beta-final-2026-10-28/next-prompt-ab-plan.json)，原文件不追改，授权单独保存并一次性消费。原计划SHA256：`01ea5cf1fee5dc62ec8baa8225f1ad70336fdaef3b66b80076c3546a3b8353a7`。

- 本机既有SiliconFlow `tencent/Hunyuan-MT-7B`，固定HTTPS直达，无中转/换服务商/换模型。
- A：正式按方向生成的原Prompt；B：仅追加此前冻结的第9/10条语义约束。每句两次、AB/BA交替，12次A+12次B。
- max_tokens=80、temperature=0、context=0、并发1、timeout=12s、禁用短语缓存与重定向。没有额外热身/真实Key测试请求。
- POST之前校验固定原文、方向、模型、参数及基线Prompt；只在独立实验HTTP适配层写入B的system消息；持久化预留计数，并拒绝重复profile。账本的Prompt与实际发送相同，由回环测试验证。
- 官方[价格页](https://www.siliconflow.cn/pricing)于UTC `2026-10-28T02:39:26.042973+00:00`实际GET 200，模型行输入/输出均为“免费”，预估24次费用**¥0**；不是账户账单核销。网页访问不属于翻译API调用。

原生Qt为源码组件真实Windows窗口，不是Full EXE，也不涉及Whisper或真实语音。源句是独立自编游戏类文本，源文/目标语人工核验均pending；完整原文及两版实际输出见[逐对审阅表](evidence/v0.5.3-prompt-ab-2026-10-28/paired-human-review.md)。

## 实测结果

| 指标 | A原Prompt | B附加约束 | 合计 |
|---|---:|---:|---:|
| 计划/实际请求 | 12/12 | 12/12 | **24/24** |
| HTTP200 / 完整stop | 12/12 | 12/12 | **24/24** |
| 超时/失败/length/未完成 | 0/0/0/0 | 0/0/0/0 | **0** |
| 非空可复制原生Qt字幕 | 12 | 12 | **24**（不是人工可理解率） |
| API调用P50/P95 | 1.168 / 2.531s | 1.122 / 1.691s | 1.160 / 2.180s |
| 文本提交→Qt更新P50/P95 | 1.178 / 2.537s | 1.125 / 1.702s | 1.169 / 2.183s |
| Provider报告prompt tokens | 3,223 | 4,195 | 7,418 |
| Provider报告completion tokens | 323 | 324 | 647 |
| 双语人工语义正确率 | 未验收 | 未验收 | 未验收 |

实际HTTP上下文P50/P95为1.155/2.176s。表中API调用时间包括客户端薄层、等槽与HTTP，**不是供应商服务端纯推理时间**。每版仅12次单轮观察，A第10/11句有约2.19/2.95s长尾；不能把B较低P95归因于Prompt加速。按同句配对，B有8/12次更慢，耗时差中位数约+28.5ms，第04/06/09句分别约慢74%/38%/31%，触及原计划20%的观察建议；单次抖动不足以判断稳定退化，授权已用满也不补跑。B输入token多972（约30%），没有测出语义收益，不能据此升为默认。没有语音结束→字幕、游戏FPS或ASR性能测量。

| 方向 | 独立源句 | A/B请求 | HTTP成功/非空字幕 | 结论范围 |
|---|---:|---:|---:|---|
| zh→en | 4 | 8 | 8/8 | 楼层/位置/条件与原英中回归，人工待审 |
| ko→zh | 2 | 4 | 4/4 | 人物/地点与数量否定，人工待审 |
| zh→ru | 2 | 4 | 4/4 | 数量/方向/禁止命令，人工待审 |
| ru→ja | 2 | 4 | 4/4 | 条件/触发时序，俄日人工待审 |
| en→zh | 2 | 4 | 4/4 | 原英中回归，人工待审 |

只有这5个方向本轮被调用；未复测其余15方向，不把结果推广为完整五语质量签收。12条文本是独立用例，24次请求不是24条独立语料。

## 关键语义复核（AI辅助）

| 新句/现象 | 实际A/B差异与判断 |
|---|---|
| 地下1层2队友、地面入口第3人、不要误认敌人 | 两版逐字相同，数字、地下/地面及否定都有表达；没有重现旧`ground floor`错法，但不能证明旧问题已经修复。 |
| 侦察兵/医务室、技术人员/弹药库 | 一句完全相同，另一句B仅多“有”；人物/地点与数量/第2门均有表达，没有关键语义收益证据。 |
| 4队友/无敌人/等撤退口令，右1狙击手/左2敌人/禁止向右开火 | 两句均逐字相同。俄语单数`снайпер`不能机械判为数量1遗漏；第一句共有`осталось`（剩下）的轻微增义疑点，待人工裁决。 |
| 第2信号之后才动、此前掩蔽 | A用`2番目`；B用`2回目`并加整句引号。时序词面均存在，B引号无必要，未见关键含义改善。 |
| 20秒未归来才关门、不得提前 | 两版均保留20秒、条件与禁止提前，措辞/强调不同；实际执行时序需俄日人工签收。 |
| 英→中“两人都离开前不得投掷” | B主要为“两个/两名、塔里/塔内”变化，否定与两人条件均有表达。另一个人物/物品上下位置例两版相同。 |
| 位置/模态共同疑点 | “楼梯下方”两版均译`downstairs by the stairs`，可能改变相对位置；“不能提前关闭”均译`cannot be closed ahead of time`，可能产生能力/禁止的模态歧义。均需语境和人工裁决，不硬判严重错误。 |

四对差异为`ab-new-04/07/08/09`；其余8对逐字相同。上表不将词面保留当作人工语义通过，也不把共同疑点算作候选新增退化。旧四条开发失败题本轮未发送，新句未覆盖所有歧义和游戏语境，**没有证据宣布旧模型问题消失**。

建议：保留正式A，B只保留实验记录，不继续为了旧题调Prompt或追加调用。本批现有材料交双语人工裁决即可；五语发布状态仍沿用[受邀技术预览决定](v0.5.3-beta-final-decision-2026-10-28.md)，本次不自动升级为Beta。

## 工具、测试与安全

- `scripts/run_prompt_ab_online.py`：冻结计划/候选与新24次授权、固定模型及价格验证、B的实验发送层、逐profile防重复；没有复制另一套翻译引擎。
- `scripts/run_beta_blocker_online.py:130`：原生Qt执行器增加可选`client_factory`，旧20次入口/默认校验不变；控制台分母改为实际计划长度。
- `tests/test_prompt_ab_online.py`：新增6项，测试24次A/B实际payload/账本一致、篡改/旧授权拒绝、限流停止、重复profile和未计划输入不发送HTTP、partial不显示。与既有18项合计**24/24零外网预检通过**。
- 没有正式运行时变更，不重复上轮633/70全量或ASR矩阵。回退仅移除独立执行器与恢复旧执行器3处工具改动；正式Prompt无需回退。
- 原用户配置前后SHA256均为`73df2586a0781971ea9f391abdab9dbc2e33401ef87d5db08e70314ce776ad5e`；旧255/20请求账本和原离线24次计划与`97d8bbfe`字节相同。Key只在进程内授权，不写入副本、日志、截图或提交。
- Runtime正常关闭、线程退出，未初始化生产遥测。**本轮24次授权已消费，不得重放或换目录补跑。**

已执行命令（在线命令仅作记录，不能再次执行）：

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest tests.test_prompt_ab_online tests.test_beta_blocker_online tests.test_five_language_online_acceptance tests.test_beta_release_blockers -q
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/run_prompt_ab_online.py --run-live --plan docs/testing/evidence/v0.5.3-beta-final-2026-10-28/next-prompt-ab-plan.json --approval build/prompt-ab-live-20261028-24.authorization.json --price build/prompt-ab-preflight-20261028/price.json --settings E:/my/my/game_voice_translator/user_settings.json --output build/prompt-ab-live-20261028-24
```

[独立证据](evidence/v0.5.3-prompt-ab-2026-10-28/)含24次账本、实际Prompt/输出/usage/延迟、授权与消费标记、价格证明、12对人工表、24张原生Qt截图、清理/配置校验及实际执行脚本字节副本。本地原始目录为`build/prompt-ab-live-20261028-24`，没有覆盖历史结果。
