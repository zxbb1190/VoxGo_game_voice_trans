# VoxGo v0.5.3 五语言 Beta 阻断项收口（2026-10-28）

基准 `5dcd75bf`，分支 `codex/multilingual-online-053`。运行时修复提交 **`f7d2c35f19ef0359e6d3c565d321d7d3c2438644`**；审阅工具、测试与本记录另行本地提交。本轮保留20方向修复，只改两个产品代码文件。没有真实翻译API请求、生产查询/迁移/部署、push、tag或发布，没有下载模型或重跑136组ASR矩阵。

已阅读10月27日的四份交付；本轮重新校验 **2,161份**既有本地产物，字节与旧索引全部相同。旧255次请求仍是旧批次，不消耗其剩余授权。新证据全部放入 [2026-10-28独立目录](evidence/v0.5.3-beta-blockers-2026-10-28/)。

## A. 发布阻断项关闭表

| 优先级 / 问题 | 本轮状态 | 证据与边界 |
|---|---|---|
| P0 日语整句无输入 | **仍存在；是否误杀有效语义证据不足** | 精确PCM、活动窗口和两策略原输出已核验。不能据供方全文给每段补标签，未改增益/捕获/语言/过滤 |
| P0 五语重大ASR错误 | **仍存在；需要人工核对** | 16条已有独立录音、26份策略结果集中复核；中文不全是繁简误差，英文最差样本包含Whisper前整段拒绝，不等于`.en`模型质量 |
| P0 四条纯文本关键含义差异 | **仍存在；待双语签收** | 均为`finish_reason=stop`，不是80 token截断、ASR或语言中转引入。未改Prompt、未硬编码译文 |
| P1 非空截断输出当完整成功 | **已修复错误处理** | `length`响应不再成为可复制字幕、成功统计或上下文。未自动重试、未提高输出上限；正常响应不变 |
| P1 切语言后旧请求仍占槽 | **已修复客户端取消/清理** | 覆盖HTTP进行中、semaphore等待、提交后尚未启动、后台线程和fallback loop。取消不作为API失败上传；原UI版本门保留 |
| P1 有效当前请求的长队列/4次HTTP超时 | **仍存在；根因未完全定位** | 本轮没有真实复测，不能声称9.78s P95已降低。无年龄TTL；慢服务器/网络/串行排队仍可能造成等待 |
| P1 不可见历史项继续消费请求 | **代码存在路径；旧批次发生量证据不足** | 浮窗fade/清空不通知Runtime取消；排队后也不检查UI条目生命期。未实施第三项产品改动，不能无条件按年龄丢短句 |
| P1 三语独立策略 | **方案已给出，未实现** | 仍为共享开关；没有擅自迁移用户默认，韩语small不因CER默认开启 |
| P1 Full EXE完整GUI/退出/更新 | **需要人工或可控原生环境** | 新包本地模型及后台启动成功；原生自动化未枚举目标窗口。完整GUI步骤未执行，清理为已核对路径的强制结束，不能记正常退出通过 |
| P1 游戏FPS、低配性能、人工可理解率 | **需要设备/人工验证** | 本轮无对应资源，不编造数据 |
| P1 63字段与生产发布顺序 | **本地兼容通过；生产条件未确认** | API 70项和客户端联合验收通过。未查询生产，仍禁止Full进入旧Worker；见C的顺序/回退约束 |

### 日语 `beta-ja-1731-10203675650837159328`

原供方参考：`群島や湖では、必ずしもヨットは必要ありません。`，**人工听音与逐词帧对齐pending**。WAV 16kHz/mono/PCM16，111,360帧/6.96s；WAV SHA256 `86036e977fa04d9c156cfcd83b751164953e9b56201e8d64eff18a20ab83103e`，PCM `340bc1f56485f7531c29c67f1f777dc10cf6f3743abc6b0667e5a9e9f3bd074e`。原FLOAT WAV SHA256 `70d05f350c3fe4585fa6be747cd00de46b84a270517527df8b271e2f0f4cca8c`。

对全部60个原FLOAT来源和现有PCM做量化核对，符合既有PCM16 round/clip；没有发现本轮准备工具多除一次音量。该文件整体RMS **−59.4dBFS**，最大120ms RMS **−50.7dBFS**。三次送Whisper的片段RMS都低于正式`min_gain_rms_dbfs=-50`，故保存的归一化增益全部为0；这是实际规则，不是本轮新配置。

| 策略 | 原WAV帧区间（依次，半开区间） | 结果 |
|---|---|---|
| legacy | `[21120,44160)` / `[44160,59520)` / `[59520,72960)` / `[72960,86400)` / `[86400,107520)` | raw依次：`그는 또야, 미...`（ko/.1598，弱置信度拒绝）/预算拒绝/空（en/.1997）/预算拒绝/`お疲れ様でした。`（ja/.9538，弱置信度拒绝）；最终译前空 |
| language_aware | `[19200,44160)` / `[44160,59520)` / `[59520,72960)` / `[72960,86400)` / `[86400,99840)` / `[99840,107520)` | raw依次：`군떡이 아님`（ko/.1115，弱置信度拒绝）/预算拒绝/空（en/.1997）/预算拒绝/`アリマッセン`（ja/.9329，avg_logprob −1.037，弱置信度拒绝）/预算拒绝；最终译前空 |

所有保存片段均逐字节重建一致，保留原回放前后3s补零和末尾chunk对齐零。两策略均无最大时长强制切段、无捕获原始队列丢块。日志VAD活动分别57,600/55,680帧，**未捕获的VAD活动帧均0**；其中19,200/21,120帧落在预算拒绝片段（1.20/1.32s）。这证明预算前有VAD活动被拒绝，**不证明对应词句有效或关闭预算即可恢复句意**。即使放行候选`アリマッセン`，也没有恢复“群岛/湖/未必需要游艇”的完整关系。

最早可观察分化：低音量输入→`SystemAudioCapture.process_audio`软静音/重新起音反复提交→部分`Pipeline.pre_asr`预算拒绝；送Whisper的部分也有空/异语/错误raw，再受弱候选过滤。没有证据证明Capture漏了上述VAD活动，也不能把全部失败归过滤。代码：`voxgo/audio/capture.py:999 process_audio`（1040–1073分支），`voxgo/asr/pipeline.py:1186 _enqueue_with_backpressure`、`:236 WeakCandidateTranscriptFilter`、`voxgo/asr/whisper_engine.py:916 _normalize_for_transcription`，均与基准`5dcd75bf`一致。

同批另外两条日语最差录音1972/1861，RMS为−63.0/−62.1dBFS，也有多次短段、预算拒绝/部分错词，说明问题并非只在1731出现；**未证明同一修复对所有录音有效**。目前不改ASR。下一步先人工确认这3条的有效语音/词边界；若确认共性，再只在离线实验中对“持续VAD活动是否应被软门限当静音”做一次单开关验证，同时回归已有负样本。不能直接取消全局预算或降低过滤。

### 五语最严重3–4条的集中材料

[逐录音/逐片段材料](evidence/v0.5.3-beta-blockers-2026-10-28/focused-asr-review.md)与[JSON](evidence/v0.5.3-beta-blockers-2026-10-28/focused-asr-review.json)包含完整参考、raw、译前文本、字符D/S/I、实际丢弃原因、精确PCM、能量/归一化和双策略配置。参考均为供方转写、未人工确认；字符对齐只是辅助，不能生成“语义正确率”。每语3条，俄语另加入最大单例退化，合计16条，不重看全部468项。

| 源语 | 选中ID尾部（完整ID在材料中） | 可见主要问题；最早可观察阶段 |
|---|---|---|
| zh | 1905/1953/1830 | 基希讷乌→`新金納物`；医院名称只保留到`阿登`；`SWAPO`缺失及选举句错词。原raw已错，部分尾段再被过滤/预算拒绝；不能全归格式 |
| en | 1972/1914/1876 | 1972三段全部在Whisper前因低置信度/voice<.25s拒绝，raw空；1914只剩`20th century.`；1876只保留`The Northern...`，其中`office.`被后过滤。未进入模型的删除不能归“base模型识别错误” |
| ja | 1731/1972/1861 | 上述整句空；1972候选丢失`ない`相关对比、仅剩`恐竜だと思う`，兼容也残缺；1861演员/舞台/观众词面破坏，异语、预算与弱过滤并存，真实语义需听音确认 |
| ko | 1894/1907/1742 | 咖喱1894候选反而丢后半句；1907候选恢复“德国/海上封锁”相关词面但句尾`시...`残缺，尾段预算拒绝；1742 small完整性明显好于base，但资源代价仍未签收 |
| ru | 1704/1885/1757/1861 | 1704后半段被识为uk并经语言门拒绝，原raw也有错；1885数词/数字有表面差异并有语法错；1757候选改善；1861候选CER17.86%→25.00%，raw出现乌克兰式字形和词替换，但该条未因此被过滤。没有继续俄语单句调参 |

中文全12条做**仅诊断**的Windows繁→简映射，micro CER从45.40%变为33.33%（105/315字符）。仅能说明约12.07个百分点对表记敏感；剩余删除/实体错误不能消除，也不能把映射分数当新验收分。英文`Twentieth`→`20th`是局部格式差异，解释不了几十字符删除。原正式分数/历史文本没有改写。

英文边界：本批为多语言base、auto、纯英文开关false；`voxgo/config/loader.py:119 _use_pure_english_model`和`:123 _active_whisper_model_size`只在en→zh且纯英文开关启用时选择`.en`路径；Fast/Ultra Low等各有原条件。`sync_language_flow:605`控制auto/强制en，`SpeechPipeline._mode_policy:985`还有不同等待策略。**本次51.39%不能代表所有英文配置，更不是`.en`实测结果。** 没有下载或复测`.en`；48项配置兼容通过不等于其本轮质量实测。

### 纯文本与输出长度复核

四条都HTTP200、`finish_reason=stop`，completion tokens分别25、59、21、14，未触80上限；请求使用正确源/目标、单跳，Prompt与请求账本一致。位置、动作时序、角色/地点类型和明确数量的差异已经在Provider输出可见，不能归Whisper。`左边两个人，别开枪`的命令受事本身有歧义，但数量2不应无声丢失。`地下一层`、韩语`힐러`作为人而非房间没有相同歧义。

同源的其它三个目标有保留地下层、治疗角色或“数到3时”语义的输出，不能由一个方向错误推出所有方向不支持；这也不是独立第二条同类题。英/俄/中→韩的`세를 세면`是另一个重复语法/数字疑点，仍待韩语人工核对。未找到足以计算系统性严重错误率的独立人工真值。

`voxgo/translation/prompt.py:1 SYSTEM_PROMPT`包含忠实、不补全、术语保留及路由规则，但没有明确逐项保留**人数/单位/否定作用域/触发时序/角色与房间区别**；没有明确游戏场景的角色消歧，而且“术语优先保留英文”不保证非英文目标的术语自然性。这是改进假设，不能证明加规则一定修好。若另开Prompt实验，只在隔离工具中比较原Prompt与通用保真规则，对新句子A/B；**正式en↔zh仍返回旧`SYSTEM_PROMPT`，回退为原`translation_system_prompt`结果**。本轮没有实现新Prompt，也没有额外API请求。

旧4条`length`全部发生在**标准原文全文A阶段**（en→ko、en→ru、ko→ru、ru→ko），不是已证实的4条屏幕B字幕。本批135条实际ASR翻译请求无`length`记录，4次超时另计。A输出可见尾句未完/词中截断。原代码同一路径会把未来B截断文本当成功，因此修的是通用风险，不编造本批屏幕截断数量。80来自`TranslationConfig.max_tokens`默认/示例配置，保存到`translation.max_tokens`，旧实验实际值也是80；当前UI没有对应的max_tokens编辑控件。本轮既未改用户值，也未全局提上限；未来若研究按输入/目标语言分配预算，应独立、可回退且同时测延迟，不能用长参考全文的截断率冒充流式短句截断率。

### 队列/超时边界

旧客户端在`GameTranslator.translate_result_with_config`入semaphore前已通过Runtime版本检查；等待槽时切语种，仍可能继续发旧POST，直到返回后才丢字幕。本次取消覆盖这个窗口。队列9.064s是客户端等待；Provider阶段包含网络、服务端和本地HTTP，不能测得纯服务端耗时。4次超时发生于已发HTTP后，无法从保存结果分离线路与服务器内部原因。

原生字幕的fade/清空只删除UI条目（`voxgo/ui/overlay_window.py:1315 _remove_translation`、`:1324 _update_fade`，`_update_translation:1302`找不到ID就不显示），没有通知Runtime；按代码存在“不会再显示但任务仍等槽/发送”的路径，旧账本没有逐时刻可见性标记，不能计算发生量。后续最小方案是**UI显式清空/已淘汰ID的生命周期通知→发送前取消校验**，先只取消未发送请求；不要新增任意年龄阈值、加并发或一律取消仍有用的短句。本轮止于前两项已验证产品修复。

## B. 实际代码修改、回退与测试

| 文件 / 函数（运行时版本f7d2c35f） | 改动与原因 | 回退 |
|---|---|---|
| `voxgo/translation/openai_compatible.py:40 translate`（92行分支） | `finish_reason=length`返回`[翻译不完整]`；原JSON保留本地诊断，不复用partial上下文。已有App错误通路显示不可复制提示，成功数不增加；使用既有`other`分类，不扩字段 | 反向撤销这一分支；正常stop/missing finish_reason路径不变。恢复旧行为会再次显示partial，故仅用于故障回退 |
| `voxgo/translation/runtime.py:61 clear_context`、`:95 translate_async`、`:234 _translate_and_publish` | 本地generation绑定提交；切语言清context时取消旧active任务，已提交未启动的旧generation也不发送；取消释放HTTP/semaphore并清理trace/旧占位，新任务不受旧取消波及。原前后revision和App UI门都保留 | 回退此提交的Runtime/test改动，恢复仅丢弃旧结果；不触及5dcd75bf的20方向修复 |
| `tests/test_beta_release_blockers.py` | 8项：用4条已保存partial文本与finish_reason重建响应结构（非原HTTP字节重放）；20方向正常返回/旧服务器省略finish_reason；非复制提示与固定failure分类；HTTP+等待槽取消；启动竞态；超时释放；真正后台Runtime与fallback loop清理 | 随修复回退，不删除旧证据 |
| `tests/test_shutdown_lifecycle.py` | 既有内部方法stub接收新增可选keyword；停机测试语义不变 | 随Runtime回退 |
| `scripts/review_beta_blockers.py` / `tests/test_review_beta_blockers.py` | 复用旧回放输入构造/编辑距离、只读16例复核；验证60原FLOAT→PCM及保存边界、显式拒绝哈希不符，生成待人工材料；3项工具测试 | 独立工具，不被正式包导入；保留产物即可停用 |

可整体 `git revert f7d2c35f` 回退这两个运行时修复；不使用reset/checkout，也不回退旧20方向提交。审核材料另交提交保留。撤销后不能继续声称截断与取消已修好。

新收到且明确`length`的结果进入已有失败类别`other`；取消不计服务商失败。没有改63字段、累计算法、授权或历史快照，没有把旧批次成功数回填成失败。

- 客户端全量 **630/630，0跳过**，51.291s；含客户端/API联合63字段、授权、累计幂等与回退验收。
- API **70/70**、`npm run build`通过，API源码仍`e369e50`。
- 英中配置 **48/48 equal**（对照afc33a67）；release preflight通过。正常EN/ZH Prompt/默认配置/OPUS未改。
- 源码原生Windows Qt组件20/20回环HTTP通过，Win32可见检查、旧revision事件拒绝、线程关闭通过，0真实API；**不是Full EXE手验**。
- 目标36项通过；早期一个新fallback测试在已有async测试loop内调用同步close导致测试错误，改为在独立线程调用后通过；原失败日志保留，未因此修改产品close实现。
- 正式`voxgo/asr/`、`audio/`、`analytics/`、`config/`、`translation/prompt.py`、`local.py`、语言路由及用户默认均无本轮diff；没有新增依赖。

Full构建：`E:\my\my\VoxGo053Beta-20261028-closeout\dist\VoxGo`；EXE SHA256 `f044647b0b3902e4c404d4d001d96e826b50a1f55829c328eaba5a78e4891c07`，EXE+`_internal` 992,209,889 bytes，非压缩下载大小。临时spec只改staging/model/dist入口路径，初次Path类型错误日志保留，纠正后构建通过，正式spec不改。后台加载本地base成功；输入为静音benchmark，产生**6次空ASR**，无实际翻译请求，不作为语音质量/真实捕获证据。

原生控制工具两次未枚举Full窗口，未使用猜测句柄/坐标。测试目录中配置期望denied，但初始化后的权威状态为**unknown、未授权Full**；无Full上传。Basic的一次外网CONNECT被仅本地代理403拦截，代理不转发任何payload；更新关闭、模型离线、没有生产Key。测试进程在路径校验后强制清理，无VoxGo进程残留；**这不算正常退出/资源优雅清理手验通过**。目录已有测试状态，不是发布成品，不要脱离隔离代理直接双击当验收。

Full人工清单（以下均未执行；组件/配置测试不替代）：

| 操作 | 必须观察 |
|---|---|
| 使用新目录、无真实Key、仅本地fixture/阻断代理启动 | 不动0.5.2安装/设置/模型；不启用Full；Basic连接不得转发；窗口可见 |
| 依次选择zh/en/ja/ko/ru，每源选四目标 | 共20方向；目标正确、同语种不出现；交换后源目标一致 |
| 保存、正常退出、重启 | 恢复所选方向/Provider；旧用户配置可读；进程与后台线程清理 |
| 在线/离线切换、非英中离线方向 | 明确不支持，不自动切服务、不下载未授权模型 |
| 本地正常/length/503/延迟fixture | 正常字幕可复制；截断/错误不可复制；length不显示partial，不自动重试 |
| fixture挂起时切源/目标，再释放旧响应 | 旧占位/结果不覆盖当前字幕；新方向能发；旧队列不继续消费 |
| 清空/过期/长时间多轮使用 | 记录当前尚未修复的不可见任务路径；不把一次启动当长期稳定 |
| 隔离检查更新与恢复旧包 | 不覆盖生产安装；已发布更新元数据仍0.5.2；Full遥测旧客户端回退限制见C |

已执行命令（工作目录为该worktree；均无真实API）：

```powershell
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/review_beta_blockers.py --manifest build/five-language-beta-20261027/corpus/manifest.json --baseline build/five-language-beta-20261027/asr --evidence docs/testing/evidence/v0.5.3-five-language-beta-2026-10-27 --output build/beta-blockers-20261028/review-r2
$env:QT_QPA_PLATFORM='offscreen'
$env:VOXGO_API_ROOT='E:\my\my\voxgo-api'
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest discover -s tests -q
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py --base-ref afc33a67 --output build/beta-blockers-20261028/en-zh-compatibility.json
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/release_preflight.py --version 0.5.3 --base-ref afc33a67
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/native_five_language_protocol.py --platform windows --output build/beta-blockers-20261028/native-protocol
# E:\my\my\voxgo-api：npm test；npm run build
```

新输出必须换目录，工具拒绝覆盖；Full临时spec/build日志与验证指纹在证据中。60来源核验不等于跑60次推理；只有Full启动附带上述6次静音推理，无新增语音基线。

## C. 五语20方向发布建议

**本轮关闭两个通用错误处理问题，仍不满足“完整五语质量验收通过”的Beta发布条件。** 可以保留20方向技术预览能力，不删路由；英中既有在线/OPUS能力继续保留。新18方向应标实验性，日语整句漏失、关键语义与人工/游戏证据未关闭前，不能标正式质量支持。

| 源\目标 | zh | en | ja | ko | ru |
|---|---|---|---|---|---|
| zh | — | 既有 | 预览 | 预览 | 预览 |
| en | 既有 | — | 预览 | 预览 | 预览 |
| ja | 预览 | 预览 | — | 预览 | 预览 |
| ko | 预览 | 预览 | 预览 | — | 预览 |
| ru | 预览 | 预览 | 预览 | 预览 | — |

“既有”不是本轮人工质量签收；“预览”均保留代码支持及上轮固定SF真实连通证据，本轮只做回环回归，没有重新真实验证。Google与其他OpenAI-compatible模型仍未真实验收。离线仅en↔zh；不开放其他18方向离线，不新增语言模型/中转/OCR。截断partial作为正常字幕已关闭；旧语言任务字幕继续禁止。20方向API成功率不能代替人工可理解率。

| 源语 | ASR建议（本轮没有改变任何用户默认） |
|---|---|
| zh | 保持当前正式普通话配置；先人工分离表记、实体与删除问题，不改全局模型/阈值 |
| en | 保持既有普通/纯英文选项及适用方向；本次base/auto弱音问题不代表`.en`结论 |
| ja | 保守候选用legacy，不据CER微降推language_aware默认；两者漏句均未解决 |
| ko | 保守候选用legacy/base；small只作显式实验，须关键含义和真实游戏/低配FPS验收 |
| ru | 保留language_aware作为实验候选；正式默认待人工实体/否定复核，legacy可回退。不再旧样本专项调参 |

产品**需要**每源语种覆盖能力才能安全采用不同发布策略。本轮未确定各语正式默认，故只提出最小兼容设计，未实施第三项产品改动：

1. `WhisperConfig`新增可选`multilingual_asr_overrides`映射，仅ja/ko/ru允许`legacy/language_aware`；空/缺失沿用旧共享字段，非法值提示并继承，不能默默变候选。
2. `language_profiles.effective_speech_config`查询当前**源**语种；EN/ZH不读取。`config/loader.py`仅在非空时序列化；旧配置保存语义不变，不迁移默认。
3. `settings_dialog.py`保留旧共享选项，增加三项“继承/兼容/候选”；显示与保存一致，保留明确兼容回退。`settings_controller.apply`、运行签名和待处理Whisper配置按生效源策略比较/深拷贝；改未激活语种不应误重置当前EN/ZH。
4. 必须测缺字段/空映射/部分覆盖/非法值、保存重启、四目标相同源策略、切换中快照、48项英中兼容、旧版本忽略新字段。旧版本重新保存可能丢覆盖，升级回来时回到共享字段语义；不能承诺无损设置回退。

63字段顺序：以本地API `e369e50`的 `tests/release-v0.5.3-rc.test.js:82/100/115` 和 `docs/testing/release-v0.5.3-rc.md` 为依据：**先核对/备份生产D1并应用0006→部署兼容Worker→验证health、Dashboard、新旧11/13/27/35/63字段、授权与ACK/幂等→最后允许候选Full**。本轮未核实生产状态，不能把本地通过视为已部署。旧Worker即使配0006仍拒63字段；新Worker配0005时health/Dashboard失败。已有63字段客户端后保留0006；不得删列、推测回填或改pending快照。不得不退旧Worker时先远端关闭Full，验证503/Retry-After而不是让63字段收到终态400；Basic独立。0.5.2客户端不能无缝解析已升级的63字段本地聚合，须保留状态并重新升级恢复，不能删状态强行上传。本轮没有进行上述生产操作。

## D. 最终小规模复测计划（待新授权）

[具体20条清单与配置](evidence/v0.5.3-beta-blockers-2026-10-28/next-online-plan.json)：**20次计划/硬上限20，0重试**；固定本机既有SF `tencent/Hunyuan-MT-7B`，只读配置，不换Provider、不购买额度。旧300次授权不复用。单次POST前记账，超时/取消也消耗次数；价格/权限/付费/限流/模型不可用或路由错误立即停止。

| 范围 | 方向 | 请求 |
|---|---|---:|
| 关键含义 | zh→en、ru→ja、ko→zh、zh→ru；每方向1条旧锚点+1条新句（地下/地面、先后时序、角色/房间、明确敌方数量） | 8 |
| 截断边界 | en→ko、en→ru、ko→ru、ru→ko；每方向1条新长句+1条短句对照 | 8 |
| 英中旧Prompt回归 | en→zh、zh→en，各2条新数字/否定/等待条件句 | 4 |

16条新句未用作本轮调参，不只有4条开发失败题；文字由AI辅助准备，源材料/目标含义仍待人工核对。max_tokens=80、temperature=0、context=0、并发1、timeout=12s、正式Prompt不变，bench禁用短语缓存。长句若自然返回完整stop则审阅全文；若length则必须提示且不显示partial，**不强求每条一定截断、不加重试凑结果**。本轮没有Prompt实验；若另测新Prompt，须重新列A/B与数量，不能偷偷将20变40。

预计¥0，依据[硅基流动官方价格页](https://siliconflow.cn/pricing)索引仍列输入/输出免费；2026-10-28直接抓取超时，未核对账户账单，执行前需再次确认，无法确认即不执行。独立目录`build/beta-blockers-online-20261028-20`；计划`authorized=false`、`execution_ready=false`，批准后才生成绑定计划哈希的一次性执行授权。没有真实Key或令牌写入材料。

判定：所有方向参数正确、无中转/静默回退；正常短句保持原Prompt行为；length不作为完整字幕/成功/context；HTTP200、stop、length、超时、取消、未完成分别报告。数字、否定、位置、时序、角色严重含义错误须双语人工裁定，AI不产人工准确率；任何严重错误继续阻断，不用20条宣称长期准确率。切语言取消/超时释放已用零外网实际Runtime/HTTP验证，不额外消耗真实请求制造长等待。**本计划仅翻译文本复测，不代替日语ASR修复、Full手验和真实游戏/FPS验收。**
