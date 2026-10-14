# VoxGo v0.5.3 Release Candidate 验收记录

验收日期：2026-10-14。结论：**本地 RC 验收通过；生产迁移、部署和正式发布未执行，不能视为已上线。** 0.5.2 客户端回退的 Full 上传限制见下文，不宣称无缝双向兼容。

## 基线与纳入范围

| 对象 | 核对结果 |
|---|---|
| 正式分类客户端 | `1fc28400dcb5b7ac9385aa81b2728b1c37da6651`，运行代码与本轮RC相同，只有APP_VERSION变为0.5.3。 |
| 正式分类API | `5f97192118f6a2e553a77bc76a8970481a3fbfc5`，本轮不改业务源码、协议或0006。 |
| 原客户端工作区 | `E:\my\my\game_voice_translator` 保持 `f78f2f6f` 和 `codex/en-zh-semantic-audit`；所有PoC/审计提交及忽略目录实验记录保留。 |
| RC隔离工作区 | `C:\Users\Administrator\.codex\worktrees\release-053-rc\game_voice_translator`，`codex/release-0.5.3-rc`，从1fc28400建立，未带入三个PoC/审计后续提交。 |
| 已发布基线 | `52d77cbf`，用于默认参数、依赖和update manifest比较；不代表本轮重新验证了远端Release。 |

本版本仅纳入四模式ASR分类诊断、API失败原因/服务商分类及对应Dashboard。RC新增内容仅为版本位置同步、验收测试与记录、中英文更新日志；release workflow使用完整Git历史，保证真实旧版本模块回归可运行。

`config.example.json`、Audio/Whisper默认值及切段预设、Prompt、翻译模型/beam/分句/术语、requirements、VoxGo.spec和已发布`docs/update.json`均保持不变。客户端运行源码相对1fc28400除`voxgo/app_info.py`版本外无差异。未集成日/韩/俄语或M2M100。

## 63字段合同与授权验收

Full仍为schema 2：既有35项＋28个固定数值计数＝63项。28项是四模式各五项（20），六种API失败原因与两个服务商（8）。内部`diagnostics_classification_reported`仅为服务端覆盖标志，不是第64个上报字段。Basic及consent version 3未变。

| 验收项 | 证据与结果 |
|---|---|
| 新旧协议及hash | v1的11/13项、v2的27/35/63项与共享canonical SHA fixture通过；缺字段、未知字段、非法值/自由文本及分类子计数越界拒绝。最大D1绑定73，低于100。 |
| 模式归属 | capture发出事件前固定mode，Pipeline入队/合并前记录；缺旧label才使用入场时设置。Fast/Balanced/Accurate/Custom均覆盖；不读当天末次设置，不把Custom推断为Balanced。 |
| 原因/服务商归属 | Google及OpenAI-compatible均覆盖timeout/network/rate_limit/http_error/empty_result/other；provider来自任务配置快照。取消、停机、过期结果与未知/本地缓存不伪归API尝试。 |
| Full授权 | 未授权、旧授权、非法授权、保存失败、跨进程撤销均fail closed；新安装完成前不启动Full。关闭不创建远端collector/uploader；重新授权遵守新epoch边界，不补传原授权前事件。 |
| Basic独立 | Basic按既有开关与日匿名ID工作，不加入分类字段；不把关闭Full等同关闭Basic。 |
| 隐私 | 仅固定数字；本轮fixture、Dashboard输出与provider错误测试均确认不带语音/字幕、API Key、地址、错误正文或安装标识展示。 |
| 累计与幂等 | 同安装日累计快照不按上传次数相加；重复、乱序、旧revision、相同revision冲突、计数下降、低版本遗漏分类列、事务失败和精确ACK均通过。队列压力、UTC跨日、撤销/重新授权保持单事件原子性。 |
| 历史口径 | 旧事件不推测mode/reason/provider，不搬到other。0006对历史新增列写默认0、marker0；无覆盖的比例为null/页面—，不能把零值视为支持新格式。 |

真实Python后台writer → AggregateStore → 有历史数据的0005 SQLite迁移0006 → Worker请求 → Dashboard聚合 → 精确本地ACK的联合测试已执行，不是只校验两份静态fixture。请求均为本地合成请求，没有发送生产遥测。

## 升级与回退：支持边界

新增`tests/test_release_053_compatibility.py`从Git加载真实已发布基线52d77cbf的aggregation/daily_metrics模块，而非在当前模块中手工模拟旧字段：

1. 0.5.2的真实35字段pending升级后，identity、pending内容/hash和revision保持不变；实际新事件才形成63字段新revision。旧ACK不能消除新pending。
2. 已存在63字段aggregate时，0.5.2因未知字段抛`invalid metrics`，**Full聚合/上传暂停**，aggregate和identity字节不变。已ACK的63字段基线/水位也同样保留，不被重置。
3. 同一授权epoch、现有7日保留窗口内重升0.5.3，可继续累计旧进程的新shard、保留分类水位并精确ACK。旧进程事件只增加全局未分类残差，不回填模式。不能把此结果称作0.5.2持续Full上传成功。

Windows updater事务测试真实执行PowerShell helper，以受控可执行fixture完成替换、失败回滚、内部模型链接物化及外逃链接拒绝；配置、模型、CUDA、授权文件、Basic/Full outbox和生命周期状态均保留。它验证的是更新事务，不是用户机器上的真实0.5.2→0.5.3 GUI使用验收。

API的旧shape兼容与Worker回退是另一层。API RC记录位于`E:\my\my\voxgo-api\docs\testing\release-v0.5.3-rc.md`：

| Worker | D1 | 健康/管理聚合 | 旧11/13/27/35 | 新63 |
|---|---|---|---|---|
| 历史012141b | 0005或0006 | 200 | 200 | 400（终止性拒绝） |
| 分类5f97192 | 0005 | 503 | 200 | 503，事务回滚 |
| 分类5f97192 | 0006 | 200 | 200 | 200 |

分发新客户端后必须保留兼容63字段的Worker和新增列。不得直接回退旧Worker让pending收到400；不可避免时先关闭Full远端开关，验证config关闭、POST为可重试503且Retry-After 900，Basic继续独立，再恢复兼容API。不要删列、重置本地identity或改写pending强行消除错误。

## 测试、打包与更新结果

| Gate | 实际结果 |
|---|---|
| 最终完整Windows客户端套件 | **492通过、0失败、0跳过，33.268秒**；VOXGO_API_ROOT指向兄弟API，联合合同测试实际运行。初始489项通过后新增3项真实旧客户端回归，再完整运行一次。 |
| API完整套件 | **70通过、0失败、0跳过**；原67项＋3项真实历史Worker/schema/kill-switch矩阵。 |
| API构建 | `npm run build`与Wrangler`deploy --dry-run`通过，非部署。 |
| D1本地迁移 | 独立本地库0001～0006成功，重复apply无待迁移；76列，29项新增INTEGER NOT NULL DEFAULT 0；历史行原值/hash/revision/时间不变。 |
| 源码/预检 | compileall、release_preflight（0.5.3，对照52d77cbf）及diff --check通过；update manifest仍为已发布0.5.2。pip check无依赖冲突。 |
| 四种归档 | Lite、Full、Full-CUDA和CUDA runtime均完成真实本地构建与SHA校验，详见下表。 |
| 冻结客户端 | 三个EXE均`--help`退出0；提取真实PYZ验证APP_VERSION 0.5.3、63 metrics/28分类字段。没有PoC、tests/scripts/diagnostics、Torch/Transformers/Datasets模块。 |
| 包内容与默认值 | 安全示例配置及package-info正确，Lite无ASR模型、Full/Full-CUDA只有正式base/small；16项模型文件校验均与0.5.2一致。三包的CT2 DLL/扩展和SentencePiece扩展共9项二进制校验均与0.5.2一致。无用户设置、遥测状态、实验模型或字幕/音频记录。 |
| 更新回归 | manifest解析、版本比较、可信下载/校验、离线提示、压缩包路径/链接防护、空间限制、准备失败清理及真实Windows替换/回滚通过。 |
| 独立只读审查 | 未发现可复现阻断级缺陷；补充并明确了旧客户端Full暂停的文档边界。 |

日志和逐文件hash位于RC工作区忽略目录`build/rc-0.5.3/`：`client-final-tests.log`、`client-rollback-tests.log`、`preflight-final.log`、`packaging.log`、`package-verification.json`。API日志位于`.wrangler/rc-v0.5.3/`。未将私有配置、遥测ID或缓存打包/提交。

正式发布流现有资产为四个ZIP；本机无ISCC，本轮未编译Inno Setup安装器，仅同步其版本。Full-CUDA完成依赖包含校验，不代表实际GPU推理验收。未运行正常GUI/真实声卡捕获或向生产发送63字段；这些限制不由`--help`或单元测试替代。

## 本地RC资产

目录：`C:\Users\Administrator\.codex\worktrees\release-053-rc\game_voice_translator\release\`。以下不是GitHub/GitCode已发布资产。

| 文件 | Bytes | SHA256 |
|---|---:|---|
| VoxGo-v0.5.3-lite.zip | 136889495 | `9d21fe32ddf2e349af7fd6635d2262c8e4091b1e0b0e4cd9f77ae9753c478450` |
| VoxGo-v0.5.3-full.zip | 716687133 | `89ce430312d3ab4c3407ff34873193e49ab22188d04c2a700f578bb40b34790b` |
| VoxGo-v0.5.3-full-cuda.zip | 1307403695 | `190313f86332c844fcb9367efcb9419d06ad7682849a187e8d35f60c3db7e781` |
| VoxGo-v0.5.3-cuda-runtime.zip | 590591465 | `49bfa15f4f7719eb75ccb5852be43ae10aa8f40ed8a7853b1d65675e25d05453` |

## Dashboard浏览器验收

使用当前真实Dashboard HTML/JS、真实getDashboardStats和内存SQLite合成数据，监听127.0.0.1；旧行先插0005再迁0006，另加classified fixture和零事件支持者。**仅本地绕过认证，不连接生产**；真实认证/会话请求另由API测试验证。

桌面浏览器7/14/30日切换与分模式/原因/服务商表均正常，无控制台warn/error。混合场景支持安装日8/15、8/22、8/38；分段事件覆盖28/70、28/105、28/185，证明格式覆盖与事件覆盖分开。纯历史7日场景模式/原因/服务商分类为0、比例—，35分段与105失败保留未分类，不进入other。相关合成Critical/Warning不是生产健康结论。

本地截图：`build/rc-0.5.3/dashboard-mixed-7.png`、`dashboard-mixed-30.png`、`dashboard-history-7.png`；HTTP六组合证据在API`.wrangler/rc-v0.5.3/dashboard-preview-http-validation.json`。验收后已关闭浏览器页并停止自建预览服务。

## 生产只读条件与发布前操作清单

API在2026-10-14 09:04～09:06 UTC（北京时间17:04～17:06）只读确认：ledger为0001～0005，0006待应用；Full表47列，分类marker/fast列缺失；Full/Basic均开、采样1、间隔900秒，health ready。三条schema查询rows_written均0、changed_db=false，未读取安装标识或写入遥测。

后续须另行授权执行：

1. 私下备份生产D1，复核0005 ledger/47列及开关/Secrets；遇部分迁移或ledger不符先停止，不手工猜补列。
2. **先应用0006**一次，检查ledger、76列、29项默认/约束与历史值不变；保留所有新增列，历史marker仍0。
3. **再部署兼容Worker**，核对health/config、旧协议ACK、Dashboard认证及历史显示，等待既有缓存失效。部署后才允许63字段验收。
4. 在受控安装、明确Full授权下产生真实事件，确认63字段精确ACK、模式切换、故障原因、撤销/重新授权及包型。合成fixture只用于本地/隔离测试，不向生产灌假计数。
5. 完成需要的正常GUI/实际设备烟测和更新验收后，才创建正式tag/推送/Release。四资产发布并核对真实大小/SHA后才更新`docs/update.json`和官网静态更新日志。
6. 回退优先保留63兼容API；不可避免旧Worker时先Full kill-switch并验证503。旧0.5.2客户端Full暂停与同epoch重升恢复须纳入支持说明。

本轮未执行生产migration、deploy、Git push、tag或GitHub Release，也未提前修改已发布更新渠道。

中英文用户更新日志：[v0.5.3 draft](../releases/v0.5.3.md)。首次配置完成率为另附只读调查，文件在原工作区`build/first-run-readonly-investigation-2026-10-14.md`，未纳入RC代码或改变统计口径。
