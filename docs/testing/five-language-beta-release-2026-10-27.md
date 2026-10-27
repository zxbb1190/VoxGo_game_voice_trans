# D. v0.5.3 多语言 Beta 发布决策与复现（2026-10-27）

**决策：技术连通候选已完成；不能作为“完整五语言20方向质量验收通过”的 Beta 发布。** 本轮完成 [A ASR](five-language-beta-asr-2026-10-27.md)、[B 20方向真实在线/字幕](five-language-beta-matrix-2026-10-27.md)、[C 阻断清单](five-language-beta-blockers-2026-10-27.md)，没有 push、tag、GitHub Release、生产 D1 migration、Worker deploy 或 R2 上传。

## 建议的支持边界与策略

| 源语言 | 最终建议状态 |
|---|---|
| 中文普通话 | 保留现有正式配置与英中能力。当前测出字面 CER/格式和翻译问题，不由本轮改 ASR/Prompt；不能借旧已发布状态给新语料质量签收 |
| 英语 | 保留正式默认及纯英文 `.en` 的既有条件；未改识别/翻译策略，48项旧配置兼容与全量回归通过 |
| 日语 | 两策略均有整段无输入，候选 CER 仅微降、CPU增加；最终发布策略未定，暂不因平均分默认推新策略 |
| 韩语 | base兼容可作低CPU内测路径；small保留显式候选，禁止在没有真实游戏FPS/关键含义验收时默认升级 |
| 俄语 | language_aware有新语料改善，值得保留候选，最终默认仍待实体/否定人工签收；不再旧样本专项调参 |

没有自动修改用户现有策略。正式发布若要混合以上选择，应先实现并回归源语种覆盖配置，不能把未验收的三语一起打开。EN/ZH 不受该配置影响。

20方向当前代码和固定 SF 模型技术上都连通；每方向3次自编文本成功返回、每方向至少有一条真实字幕。**四个日语源方向有语音用例失败，其他方向即使3/3非空也未完成质量签收**；中→英、韩→中、俄→日等纯文本含义差异见 C，不以“接口支持”替代质量支持。

离线 OPUS-MT 仍仅 en↔zh。其余18方向只允许用户自行配置在线 Provider，没有新增日/韩/俄离线模型、官方 API、付费/积分、OCR、降噪或音源分离。Google和其它兼容模型只做契约核查，真实质量未验收；不能推广本轮 SF 结果给所有服务。

可保留内部技术预览分支与独立测试包；正式对外称完整五语 Beta 前，须关闭 C 中的关键语义/日语漏句问题、补人工可理解率与游戏证据。每方向3例是阻断探索，不是长期准确率样本量。

## 本地代码变更与兼容性

- `voxgo/languages.py`：20方向及 `zh_CN` 兼容；未知/相同新语种方向仍拒绝，离线仍2方向。
- `voxgo/asr/language_profiles.py`：已有三语源配置应用至新增六目标组合，数值不变。
- `voxgo/ui/config_models.py`：中英文离线限制说明覆盖所有其他方向，不自动改 Provider。
- 复用 `offline_russian_capture_ab.run_child` / `offline_asr_observer`；缓存模型解析改为支持实际 active model，避免将韩语 small 错测成 base。旧 RU 工具默认路径仍保留。
- 新数据准备、五语离线/原生协议/受控在线/汇总工具与对应测试；这些实验脚本和语料不进入 Full 包。

未修改 `voxgo/translation/`、正式捕获/Whisper引擎、Audio preset、正式模型/beam/Prompt/过滤/OPUS术语、`voxgo/analytics/` 或默认配置。旧14方向 Audio/Whisper参数全等；与 `afc33a67` 英中 48/48 相等。API仓库仍 `e369e50`，原有未跟踪根 `AGENTS.md` 与 `.codex/` 目录均未改。

采集开始 HEAD `1d187daa`；证据包含采集时逐文件指纹与源码副本。本地交付提交见最终答复 / `git log -1`。离线采集完成后仅补齐中文离线提示文案，不改变 ASR；真实在线执行使用该最终运行时代码，脚本字节副本也已归档。保留历史所有实验，不改旧证据。

## 实际验证

| 检查 | 结果 |
|---|---|
| 客户端全量，包含本地客户端/API联合验收 | **619/619通过，0跳过**（48.356s） |
| API本地单测 / build | **70/70通过 / 通过** |
| 英中基线配置 | **48/48 equal** |
| 发布静态 preflight | 通过；默认配置/preset/Prompt profile/依赖/更新元数据不变 |
| 离线ASR | 136/136新进程排空，包含96语音策略与40噪声策略运行 |
| 原生协议 | windows QPA + Win32可见检查，20/20方向回环真实HTTP；旧版本事件拒绝，0真实API |
| 完整本地链路保护 | 正式Whisper/捕获/过滤→回环→原生Qt通过，4次回环请求，0真实API；单独标为协议，不计质量独立样本 |
| 真实在线/原生语音 | 60/60进程完成，255/300请求，251完整200、4超时、0未完成；无重试/换服务商，设置哈希不变 |
| 文件/进程复核 | 85原文件和WAV/PCM校验，**727片段**逐字节对应回放流；196份离线/在线进程结果全部正常关闭 |
| 隐私 | Key只在现有配置读取后保留内存，未复制进候选/日志/报告；只发送自编/公开参考与ASR文本；Analytics未初始化，无生产私有内容上传 |

本地联合测试用内存 SQLite/Worker请求验证新旧字段、授权与幂等，不是生产迁移。619项中包含63字段相关回归；本轮没有更改协议或口径。生产0006/兼容Worker就绪状态未在本轮操作，**不得让候选63字段Full直接进入旧Worker**。未来需另行授权并按 D1兼容迁移→兼容Worker→验证→客户端Full放行顺序处理，本轮不做。

首次本地全链路保护的观察器引用错误在0真实API阶段暴露，修正后换新目录完整复测，失败日志也保留；没有把它混为在线失败重试。

## 独立 Full 产物

目录：`E:\my\my\VoxGo053Beta-20261027-20dir\dist\VoxGo`。

- 目录总量 **992,209,210 bytes**（不是ZIP下载体积）；EXE SHA256 `9ee06cf9e204e452e8a203c6423bdaa8626eceb6dbc87f02fad37f8106098f91`。
- base/small 多语言模型与已有缓存哈希一致；不含 `.en`、日韩俄离线翻译模型或实验脚本/语料，没有新增运行依赖。
- 打包仅用新建短路径 staging/dist/work；不覆盖旧安装、0.5.2用户设置和模型。初次长路径复制模型失败日志保留，短路径重建没有改包内容。
- `_internal/config.json` 为公开示例占位Key，未复制真实用户配置；`--help` 本机执行退出0，未启动完整客户端/生产上传。
- **源码 native Qt结果不能代替 Full EXE完整GUI/更新实机手验**。不要为验收把真实Key写进报告/提交或开启生产Full。后续应使用受控本地配置/遥测隔离环境再进行完整程序手验。

## 人工与实机场景待办

1. 使用证据 `paired-human-review.json`，逐方向听完整来源WAV；填写转写、关键实体/数字/否定/时序、实际字幕可理解性和等级，审阅人签名。A全文/B片段上下文不同，勿将所有差异归Whisper。
2. `human-asr-segment-review.json` 复核被丢弃的有效语音与疑似噪声放行，保留不确定项。确认日语整段丢失源音，不全局降阈。
3. 人工给出原WAV真实语音结束帧后，可由 `source_wav_end_to_widget_ms + (WAV总帧数−人工结束帧)/16` 补算声音结束→Qt时延，无需重新请求API；物理显示仍需另测。
4. 新授权真实游戏录音补开黑/剧情/快语速/多人/噪声覆盖。用户本轮明确无法安排游戏，**FPS、卡顿和真实游戏稳定性未完成**；不能把i7桌面、限线程或回放当低配实测。
5. Full EXE原生设置/持久化/切源切目标/错误提示/浮窗/更新隔离验收；尤其在未完成请求时切语种，验证旧结果不显示、队列不积压。现有unit与组件协议不能代替这一项。

简洁评审表（数据已填在JSON，人工列留空）：

| 方向/录音ID | 来源/许可/WAV | 参考原文 | 实际Whisper及过滤 | A标准译文 / B字幕 | 末PCM→Qt / 人工语音结束 | 关键含义/问题等级 | 审阅人 |
|---|---|---|---|---|---|---|---|
| 每方向3条，15条音频跨4目标 | 已保存 | pending核对 | 已保存 | 已保存；不能视作人工真值 | 已测代理值 / 待填 | 待填 | 待填 |

真实游戏建议固定回放或训练场：同一场景、分辨率/画质/FPS上限，先游戏单独运行，再分别叠加base兼容、小模型候选及在线链路；用同一工具保存frametime/P50/P95、1% low、进程CPU/RSS、字幕延迟和卡顿事件。应记录实际设备/驱动与顺序，多次成对运行但不当作新增语义样本。本轮没有生成FPS数字。

## 复现命令与证据

工作目录 `C:\Users\Administrator\.codex\worktrees\multilingual-online-053\game_voice_translator`；以下是**已执行命令**，不要直接重跑真实API。工具拒绝旧输出目录；新在线批次需独立计划/授权，不为改善统计重试本批。

```powershell
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/prepare_five_language_beta.py --output build/five-language-beta-20261027/corpus --download
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/run_five_language_asr.py --manifest build/five-language-beta-20261027/corpus/manifest.json --models-directory .models --output build/five-language-beta-20261027/asr
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/native_five_language_protocol.py --platform windows --output build/five-language-beta-20261027/native-protocol
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/run_five_language_online.py --run-live --plan build/five-language-beta-20261027/online-plan.json --approval build/five-language-beta-20261027/online-authorization.json --settings E:/my/my/game_voice_translator/user_settings.json --manifest build/five-language-beta-20261027/corpus/manifest.json --models-directory .models --output build/five-language-beta-20261027/online
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/summarize_five_language_online.py --plan build/five-language-beta-20261027/online-plan.json --manifest build/five-language-beta-20261027/corpus/manifest.json --results build/five-language-beta-20261027/online --output build/five-language-beta-20261027/online-summary
$env:VOXGO_API_ROOT='E:\my\my\voxgo-api'
$env:QT_QPA_PLATFORM='offscreen'
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest discover -s tests -q
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py --base-ref afc33a67 --output build/five-language-beta-20261027/en-zh-compatibility.json
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/release_preflight.py --version 0.5.3 --base-ref afc33a67
# API仓库中：npm test；npm run build（均本地）
```

Full打包为原 `VoxGo.spec` 的临时路径副本，只有配置/模型staging和Analysis入口绝对路径调整；详见 `package-build-plan.json` / `package-build.txt`，原spec未改，离线环境下执行：

```powershell
$env:INCLUDE_MODEL='1'; $env:INCLUDE_CUDA_RUNTIME='0'
$env:HF_HUB_OFFLINE='1'; $env:TRANSFORMERS_OFFLINE='1'; $env:PIP_NO_INDEX='1'
.\.venv-win\Scripts\python.exe -B -m PyInstaller --noconfirm --distpath E:/my/my/VoxGo053Beta-20261027-20dir/dist --workpath E:/my/my/VoxGo053Beta-20261027-20dir/work E:/my/my/VoxGo053Beta-20261027-20dir/VoxGo-Full-beta.spec
```

[证据目录](evidence/v0.5.3-five-language-beta-2026-10-27/)含Manifest/来源许可、136+60份压缩原始结果与事件、全部255请求账本、文本输出、配对人工表、AI疑点、原生截图、测试/打包日志及验证结果。本地音频与全部产物路径/哈希在 `local-artifact-index.json`；临时签名音频URL缓存不入Git，音频/模型/EXE不入Git。原始实验均保留，不覆盖旧证据。真实请求结束后仅强化工具的一次性授权/输出绑定与防重放保护，本地7项保护测试通过，没有重发任何真实请求；证据保存的在线采集源码为实际运行版本。
