# v0.5.3 受控在线验收入口准备（2026-10-26）

对象为 `caed9130` Full。仅新增Windows验收工具，不改正式EXE、ASR模型/参数、Prompt、翻译策略、英中OPUS或63字段Telemetry。独立物理副本位于 `E:\my\my\VoxGo-0.5.3-Online-Acceptance-caed9130`；旧0.5.2和LOCAL-ONLY ZIP保留。**本文入口准备/修复阶段未发出真实API请求。随后用户实际运行记录14次上游尝试（13个200、1个网关超时），见[用户在线初测](online-user-smoke-2026-10-26.md)；三语质量与完整屏幕字幕延迟仍未通过验收。**

## 用户启动失败修复：口令原子写回

用户启动在线入口时在 `Set-LocalAcceptanceToken` 的 `File.Replace` 报“路径的形式不合法”，finally清空口令也触发同一错误。此前12项回归未执行口令实际写回路径，不能视为完整启动链路通过；此处补齐遗漏。

原生Windows PowerShell下已独立复现：第三参数传 `$null` 时原目标保留、替换失败；改为 `[NullString]::Value` 后成功。`File.Replace` 的备份参数必须为真正的null才能不创建备份，见 [微软API说明](https://learn.microsoft.com/en-us/dotnet/api/system.io.file.replace?view=netframework-4.8.1)。修复保留同目录原子替换，不退化为先删除目标；finally清理失败遗留的临时文件。

新增真实文件系统回归覆盖：含中文/空格路径、口令首次写入/轮换/清空、未知设置/Unicode完整保留、目标文件被占用时原文件逐字节不变且无临时文件残留。连同原网络边界测试，**14/14通过，12.405秒**。已更新用户正在使用的 `control/OnlineAcceptance.Common.ps1`，在实际E盘候选目录完成本地测试口令写入/还原，清理4个已核对仅含空Key/本地口令的旧临时文件。原用户配置未变，Full仍denied、候选Key为空，只读预检通过。

本次未启动持真实Key的relay、未启动在线GUI、未调用真实API。用户只需关闭旧报错窗口，重新运行同一 `Start-ONLINE-REAL-API.cmd`；无需重新解压。[修复证据](evidence/v0.5.3-online-entry/token-write-fix.json)。从源码顺序推断，用户这次失败发生在relay健康检查之后、GUI启动之前，不能归因为翻译供应商错误。

## 授权与免费模型

用户本轮要求先完成在线入口准备，明确不考虑预算，指定硅基流动 `tencent/Hunyuan-MT-7B`。按此取消本入口的金额及请求数量上限，不沿用旧脚本60次限制；保留每次尝试的本地记录、固定模型和服务商，不增加付费兜底或自动换模型。

[硅基流动官方价格页](https://siliconflow.cn/pricing)的搜索结果列该模型输入/输出免费；直接页面抓取超时。因此仅记录官方列价，不声称核对了账户账单或保证未来费率。旧 `validate_multilingual_live.py` 的限额/计价与历史记录保持原样；新入口独立实现，不改写旧60次结果。

## 使用入口

1. `Preflight-ONLY-NO-API.cmd`：只读检查EXE、配置与既有凭据可用性；不启动客户端/relay、不调用API。
2. `Start-ONLINE-REAL-API.cmd`：供后续真实在线验收，显式传入 `-RunOnline`。启动前关闭其它声音应用、退出其它VoxGo；此入口启动真实实时翻译，只播放获授权公有材料。启动器控制台保持打开，用VoxGo正常退出。
3. 客户端仍为OpenAI-compatible，地址 `http://127.0.0.1:17854/v1`，模型 `tencent/Hunyuan-MT-7B`。Key栏由启动器写入临时本机会话口令，退出清空；不要粘贴服务商Key、改外部地址或开启Full。手机服务只绑定127.0.0.1:18766。
4. 后续逐语种播放 `Play-JA/KO/RU.cmd`，结束后运行 `Collect-Diagnostics.cmd`。材料仍是9条FLEURS真人公开朗读，不是游戏/剧情/多人开黑。完整操作及安全边界见独立目录 `README-ONLINE.md`。

启动器默认只读使用本机既有 `E:\my\my\game_voice_translator\user_settings.json`。读取后严格核对服务商、固定模型、官方HTTPS地址及Key存在；不显示Key、不复制到候选设置、命令行、日志或报告、不修改原配置。缺失/不匹配时拒绝，不自行更换。测试文件中没有真实Key。

## 网络与授权边界

客户端只连本机relay；独立进程读Key并只向固定 `https://api.siliconflow.cn/v1/chat/completions` 发请求，正常校验证书、不跟随HTTP重定向。只接受会话认证的标准五字段翻译载荷及固定模型；不更改原始payload或Prompt。没有通用URL转发、CONNECT隧道、工具调用或模型替换接口。

Full初始配置、用户设置和持久授权都必须denied、epoch为空；本机拒绝代理通过候选子进程环境设置，拒绝CONNECT、Telemetry路径和任意URL代理。生产Worker不会收到该受控流程中的63字段Snapshot。正常退出后清空本地口令、结束持Key的helper；helper意外退出时只停止启动器创建的那个候选子进程。候选GUI正常保存使用设置白名单，未写回的下载/绑定保护继承明确的测试基线，显式不安全覆盖仍拒绝。

这不是OS沙箱：aiohttp不默认使用环境代理，不保证用户任意修改运行中Provider、地址或Key后的行为。必须保持上述本机配置。未改系统代理、防火墙、执行策略或安装任何新运行依赖；relay使用Windows PowerShell和系统.NET。

## 计数、诊断与时延口径

`evidence/online-relay.jsonl` 每次HTTP前先落 `attempt_reserved`，再写状态/耗时/数字token usage；包含失败/超时，没有应用层自动重试，上游并发1。写账本失败则不发请求。中断发生在落盘和发送之间时可能高估实际请求量，所以不是账单。日志不含请求/响应正文、Key、音频或安装标识。`app.log`仍可能包含识别/译文，须检查后再分享，不向生产上传私人内容。

网关路径额外经过本机HTTP与.NET上游请求，连接复用策略也与原aiohttp直连不同；后续结果必须标为“受控网关路径”，不能直接宣称正式直连性能。relay请求时长与 `[延迟] total` 都不是语音结束→可见字幕。真实屏幕端到端还需同时间轴录音/录屏；分语种记录样本量、失败、原始值与小样本限制，不相加阶段P95。

## 本轮验证与限制

| 项目 | 结果 |
|---|---|
| 本地回归 | 新在线入口10项＋原LOCAL-ONLY 2项＝12/12通过，11.886秒；6组危险配置子案例另计在一个测试方法内。没有重跑整套客户端/API测试，正式运行源码未变。 |
| 正式Provider协议 | 真 `GameTranslator` → 本机relay → 内存假上游，日文源/中文目标、Prompt、max_tokens等载荷保留；fixture响应不是质量证据。 |
| 边界 | 原生PowerShell helper用假凭据启动、健康检查/CONNECT拒绝通过；63键Full经HTTPTransport被拒绝；错误模型、错误口令、任意URL、未知字段、浏览器Origin/重复头/chunked/超大声明长度均不转发。 |
| 故障/无限额 | 账本写入失败不调用；繁忙、上游HTTP错误和异常无应用层重试；65次内存假请求完成，证明没有旧60次上限。所有请求均为本机fixture，不是65次真实API。 |
| 实包预检 | 原始EXE hash一致；8个正式模型文件和3个缓存元数据逐项hash一致；无junction/reparse point；原用户设置和原LOCAL-ONLY ZIP hash未变；测试目录扫描没有真实Key。 |
| 真实Key进程探测 | 自动审批拒绝启动读取真实Key的relay做健康检查，仅提示 `blocked by policy`，未执行、未用真实凭据重试。改为假凭据验证同一helper脚本。 |
| 仍未完成 | 真实服务商联通、这个在线入口下的GUI/声卡链路、三语人工质量、完整屏幕字幕延迟、游戏/FPS、长稳和低配真机。不能将此前LOCAL-ONLY GUI通过移作在线通过。 |

证据：[文件核验](evidence/v0.5.3-online-entry/verification.json)、[预检](evidence/v0.5.3-online-entry/preflight.json)、[测试摘要](evidence/v0.5.3-online-entry/tests.json)。原始fixture测试日志只留本地 `build/multilingual-online/windows-online-entry-tests.log`。未部署、迁移、push、tag或发布，未启动实际在线GUI或发送真实请求。
