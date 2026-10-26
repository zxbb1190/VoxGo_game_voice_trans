param(
    [Parameter(Mandatory=$true)][string]$LocalOnlyZip,
    [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference = 'Stop'
$zipPath = (Resolve-Path -LiteralPath $LocalOnlyZip).Path
$target = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $target) { throw 'Destination already exists; use a new directory. No existing installation is overwritten.' }
$expected = '55465af34fa4341bb79907e2d23c03e1ec1820154fe6a056103fbadfd99ce3b6'
if ((Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) {
    throw 'Source differs from the verified pristine LOCAL-ONLY acceptance ZIP.'
}
New-Item -ItemType Directory -Path $target | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    foreach ($entry in $archive.Entries) {
        $name = $entry.FullName
        $keep = $name.StartsWith('candidate/') -or $name.StartsWith('materials/') -or $name -cin @('control/Play-Audio.ps1', 'control/Collect-Diagnostics.ps1', 'Play-JA.cmd', 'Play-KO.cmd', 'Play-RU.cmd', 'Collect-Diagnostics.cmd')
        if (-not $keep -or $name.EndsWith('/')) { continue }
        $file = [IO.Path]::GetFullPath((Join-Path $target $name))
        if (-not $file.StartsWith($target + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive path escapes destination.' }
        New-Item -ItemType Directory -Path (Split-Path -Parent $file) -Force | Out-Null
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $file, $false)
    }
} finally { $archive.Dispose() }
$control = Join-Path $target 'control'
foreach ($name in @('Start-OnlineAcceptance.ps1', 'OnlineRelay.ps1', 'OnlineAcceptance.Common.ps1', 'SiliconFlowRelay.cs')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $control $name)
}
$candidate = Join-Path $target 'candidate'
foreach ($name in @('acceptance.config.json', 'user_settings.json', '_internal/config.json')) {
    $file = Join-Path $candidate $name
    $value = Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json
    $value.translation.provider = 'openai_compatible'
    $value.translation.model = 'tencent/Hunyuan-MT-7B'
    $value.translation.endpoint = 'http://127.0.0.1:17854/v1'
    $value.translation.api_key = ''
    $value.websocket.port = 18766
    $value.websocket.mobile_url = 'http://127.0.0.1:18766/mobile'
    [IO.File]::WriteAllText($file, ($value | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
}
New-Item -ItemType Directory -Path (Join-Path $target 'evidence') | Out-Null
$liveCmd = "@echo off`r`necho REAL online translation: fixed SiliconFlow Hunyuan-MT-7B. Close other audio first.`r`npowershell.exe -NoLogo -NoProfile -File `"%~dp0control\Start-OnlineAcceptance.ps1`" -RunOnline`r`nif errorlevel 1 pause`r`n"
$checkCmd = "@echo off`r`npowershell.exe -NoLogo -NoProfile -File `"%~dp0control\Start-OnlineAcceptance.ps1`"`r`npause`r`n"
[IO.File]::WriteAllText((Join-Path $target 'Start-ONLINE-REAL-API.cmd'), $liveCmd, [Text.Encoding]::ASCII)
[IO.File]::WriteAllText((Join-Path $target 'Preflight-ONLY-NO-API.cmd'), $checkCmd, [Text.Encoding]::ASCII)
$readme = @'
# VoxGo 0.5.3 独立在线验收入口（caed9130）

本目录为新建物理副本，原0.5.2、LOCAL-ONLY包和正式EXE未改。当前只完成入口准备，不代表三语质量或完整字幕延迟通过。

1. 先正常退出其它VoxGo，关闭其它会发声的应用，避免私人声音被实时识别并发给服务商。
2. `Preflight-ONLY-NO-API.cmd` 只检查配置/EXE，不启动客户端、不调用API。
3. 准备实测时再双击 **Start-ONLINE-REAL-API.cmd**。此入口会开始真实在线翻译；启动器控制台保持打开，结束时用VoxGo正常退出。
4. 客户端Provider保持OpenAI-compatible，地址 `http://127.0.0.1:17854/v1`，模型 `tencent/Hunyuan-MT-7B`，Full始终关闭。不要改地址/模型、粘贴真实Key或开启更新/下载。运行时Key栏是临时的本机会话口令，结束后清空；不是服务商Key。
5. 选择日/韩/俄→中文，分别使用 Play-JA/KO/RU.cmd 播放带许可的真人公开朗读。原文/来源见materials；这些不是游戏、剧情或多人开黑材料。
6. 退出后运行Collect-Diagnostics.cmd。本地app.log可能含转写/译文，分享前检查；不会自动上传这些内容。

真实Key只由独立转发进程只读加载本机既有 `E:\my\my\game_voice_translator\user_settings.json`，不复制到本目录、命令行、日志或报告；文件必须已经配置硅基流动和指定模型。换配置路径可用 `powershell.exe -NoProfile -File .\control\Start-OnlineAcceptance.ps1 -CredentialSettings '实际路径' -RunOnline`，模型/服务商限制仍生效。不要发送Key给他人。

## 隔离和记录

- 只监听127.0.0.1:17854，唯一上游固定为 https://api.siliconflow.cn/v1/chat/completions、唯一模型为tencent/Hunyuan-MT-7B。只接受本机会话认证的标准翻译请求，不改Prompt/载荷/ASR或自动换模型。
- 子进程HTTP(S)代理继续拒绝CONNECT、任意URL和所有Telemetry路由；没有通用网络转发或HTTP重定向。Full配置/持久授权均须denied、epoch为空；现有63字段协议不变。
- 这是受控流程和进程代理，不是操作系统沙箱。不要运行中改成真实地址/Key；aiohttp默认不使用环境代理，任意修改配置不在隔离保证内。没有改系统代理、防火墙或执行策略。
- 按用户要求不设金额或请求数量上限。每次上游调用先落本地账本，包含失败/超时，无自动重试、并发上游1。没有免费状态的自动抓取或付费兜底，不把“免费”当质量证明。
- `evidence/online-relay.jsonl` 只记录固定模型、时间、尝试序号、HTTP状态、上游耗时和数字usage，不记录Key、请求/响应正文或安装标识。reserved在HTTP前落盘，极端中断可高估实际发送数；不是账户账单。健康检查和预检不触发真实请求。
- relay耗时来自.NET上游HTTP请求，客户端到relay为aiohttp本机HTTP，多了一层转发且连接复用策略与客户端直连不同；测量必须标注网关路径，不能直接当作直连正式版本性能。app.log的total从分段入队开始，也不等于语音结束→实际可见中文字幕，完整字幕延迟还需同时间轴录音/录屏验收。

不执行生产D1迁移、Worker部署、push、tag或发布。没有通过双语人工/真实游戏验收的语言不宣称可发布。

2026-10-26入口准备：无外网回归12/12通过，原生OnlineRelay脚本用假凭据启动并拒绝CONNECT通过；实包只读预检通过。持真实Key进程的自动健康检查被自动审批拒绝（仅提示blocked by policy），未执行；没有重试该真实凭据动作，没有启动在线GUI或发出真实翻译请求。服务商真实联通和新的GUI链路仍待实测。

同日启动脚本修复：用户实启发现PowerShell将File.Replace备份参数的$null转换为空字符串，口令写回失败。现已改用真正CLR null，补齐口令写入/轮换/清空、中文空格路径和失败清理回归，14/14通过。实际E盘目录写入/还原与预检通过；关闭旧报错窗口重新运行在线入口即可，不需改配置。本次修复没有启动在线GUI或调用真实API。
'@
[IO.File]::WriteAllText((Join-Path $target 'README-ONLINE.md'), $readme, [Text.UTF8Encoding]::new($false))
[ordered]@{ prepared_utc=[DateTime]::UtcNow.ToString('o'); candidate='caed9130'; source_zip_sha256=$expected; source_zip_unchanged=$true; independent_physical_copy=$true; real_api_requests_during_preparation=0; credential_copied=$false; full='denied'; request_limit=$null; budget_limit=$null; model='tencent/Hunyuan-MT-7B' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $target 'online-preparation.json') -Encoding UTF8
Write-Output ('Prepared isolated online acceptance directory: ' + $target)
