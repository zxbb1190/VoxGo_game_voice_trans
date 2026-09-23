# 发布流程

1. 更新 `voxgo/app_info.py`、`installer/VoxGo.iss` 和 `scripts/build_portable.ps1` 的版本号。
2. 在 `.github/workflows/publish-release.yml` 中同步版本示例和发布说明。
3. 发布说明必须同时填写 `notes_zh` 和 `notes_en`；`docs/update.json` 的下载地址、版本号和 SHA256 必须指向同一个 tag。
4. 运行 Windows 全量测试、`git diff --check`，并用 Windows 便携包验证启动、托盘和更新替换。
5. 提交 `main`，创建并推送 `vX.Y.Z` 标签。GitHub Actions 会构建 Lite、Full、Full-CUDA、CUDA runtime，上传 Release 后再更新 `docs/update.json` 和官网链接。
6. 核对 Release 四个附件、SHA256、双语清单和官网部署状态。更新弹窗按用户设置的语言读取对应的 `notes_zh` 或 `notes_en`，不要在弹窗增加语言切换。

更新器会保留配置、Whisper/离线翻译模型和 CUDA 运行库；首次从不支持应用内更新的旧版本升级仍需手动下载。

## GitCode 国内 Lite 镜像发布规则

### 发布边界

- GitHub 是客户端源码、构建和正式发行版的来源；GitCode 仓库 `zxbb1190/VoxGo` **只发布发行版和 Lite 附件，不上传、推送或同步客户端源码**。
- GitCode 创建版本 tag 时，`target_commitish` 使用该镜像仓库现有 HEAD 的 40 位 SHA，不使用 GitHub 客户端提交，不向 GitCode 执行 `git push`。读取 HEAD 的 `git ls-remote` 不上传代码。
- 每次发版上传 GitHub Release 中的同一份正式 `VoxGo-vX.Y.Z-lite.zip`，不得用 Preview 包替代，也不得为 GitCode 单独重新打包。
- Full、Full-CUDA 和 CUDA runtime 仍仅使用 GitHub；`docs/update.json` 保持 GitHub 下载来源，国内镜像不改变客户端自动更新来源。
- 国内下载地址固定为：`https://gitcode.com/zxbb1190/VoxGo/releases/download/vX.Y.Z/VoxGo-vX.Y.Z-lite.zip`。

### 凭据配置

- 自动发布：在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 配置 Secret `GITCODE_TOKEN`，使用有权在 `zxbb1190/VoxGo` 创建发行版、上传附件的 GitCode Token。
- 本机补发：脚本从当前进程环境变量 `GITCODE_TOKEN` 读取凭据。可临时从本地 `docs/gitcode-token.txt` 载入，该文件只能包含 Token；确认 `git check-ignore docs/gitcode-token.txt` 命中忽略规则且文件未被跟踪后再使用。
- 本地 Token 文件不等于 GitHub Actions Secret；本机发布成功不能视为 CI 凭据已经配置。
- Token 不得写入源码、发布说明、命令参数、日志或 Git 提交；不得打印文件内容。用完清除当前进程临时环境变量。

### 自动发布链路

1. GitHub Actions 完成测试、正式包构建、双语说明及 SHA256 计算，发布 GitHub Release。
2. `Sync GitCode Lite mirror` 步骤读取 Secret 和镜像仓库现有 HEAD，调用 `scripts/publish_gitcode_release.py`。
3. 脚本先核对本地 Lite ZIP 与 GitHub SHA256，再查询或创建同版本 GitCode Release，取得预签名上传地址并 PUT 上传原文件。
4. 脚本从官网实际使用的固定国内下载 URL 执行完整 GET 下载，核对字节数及 SHA256 一致后，工作流才设置 `GITCODE_MIRROR_VERIFIED=true`。
5. 官网更新步骤据此更新中英文页面的国内链接和显示版本。GitCode 同步失败不阻断已发布的 GitHub 更新清单；缺少 Token 或验证失败时，明确报告镜像待补发，保留并标注上一版国内镜像，不提前放出新版本链接。

已有同名附件仅在下载校验一致时跳过；文件大小或 SHA256 不一致必须报错，不得覆盖不同文件或强行视为成功。重试前先排查失败原因。

### 本机补发步骤

1. 下载本版本 GitHub 正式 Lite 附件，准备该发行版的 UTF-8 双语说明和 GitHub 公布的 SHA256。
2. 在仓库根目录执行下列 PowerShell 示例，替换版本、附件路径、说明路径和预期哈希：

```powershell
$tag = "vX.Y.Z"
$zip = "release/official-$tag/VoxGo-$tag-lite.zip"
$notes = "release-notes.md"
$expectedSha256 = "<GitHub正式Lite附件的64位SHA256>"

$mirrorHead = git ls-remote https://gitcode.com/zxbb1190/VoxGo.git HEAD
if ($LASTEXITCODE -ne 0 -or -not $mirrorHead) { throw "Cannot resolve GitCode mirror HEAD" }
$mirrorCommit = ($mirrorHead -split '\s+')[0]

try {
    $env:GITCODE_TOKEN = (Get-Content -LiteralPath docs/gitcode-token.txt -Raw -Encoding UTF8).Trim()
    .\.venv-win\Scripts\python.exe scripts/publish_gitcode_release.py `
        --tag $tag --zip $zip --notes-file $notes `
        --sha256 $expectedSha256 --target-commitish $mirrorCommit
    if ($LASTEXITCODE -ne 0) { throw "GitCode mirror synchronization failed" }
} finally {
    Remove-Item Env:GITCODE_TOKEN -ErrorAction SilentlyContinue
}
```

3. 脚本成功后，将 `docs/index.html` 和 `docs/en/index.html` 中首屏、Lite 下载卡片的 GitCode URL 和显示版本一并更新。只提交指定官网文件，不包含 Token、诊断快照或本机配置。
4. 推送官网改动，等待 Pages 部署成功，再从线上中英文页面核对各两个国内入口均指向本版本。

### 发版完成检查

- GitCode 同版本发行版及 Lite 附件存在；固定下载 URL 可实际 GET 下载。
- GitCode 下载文件与 GitHub 正式附件的大小、SHA256 完全一致。**不能仅靠 HEAD 判断可用性**：本次验证中 GitCode HEAD 返回 401，而有效旧版 URL 的 Range GET 返回 206；最终以完整 GET 和哈希校验为准。
- 中英文官网均已部署正确的国内版本链接和标签；GitHub 更新清单保持正确，不被镜像失败拖住。
- GitCode 仓库源码分支未改变，没有上传客户端源码；Token 文件未被 Git 跟踪或提交。
- 若镜像仍失败，状态必须写明“GitHub 已发布，GitCode 待补发”，不能宣称双源发版全部完成。

### v0.5.1 验证记录

2026-09-23 已使用本机 Token 文件完成 GitCode v0.5.1 Lite 发布，未上传客户端源码；附件大小为 `137456522` 字节，SHA256 为 `5bade5ef1f90c4eb22e17719bbaadc5edf23d2d65e507b4b9e1ef2660b9468c9`，与 GitHub 正式包一致。中英文官网国内入口已更新并部署。此记录不代表后续版本的镜像或 GitHub Actions Secret 已就绪，每次发版仍须执行上述检查。
