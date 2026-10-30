# 发布流程

## v0.6.0 多语言展示同步（本次按四附件工作流执行）

产品文案统一为：五语言识别、20个在线翻译方向；日语、韩语、俄语标为 Beta，表示持续优化，并非未开放。离线 OPUS 仍仅英中双向。本次已获发布授权，按现有工作流构建 Lite、Full、Full-CUDA 和 CUDA runtime；实际 Release 及附件校验通过后同步官网、README 和更新清单。GitCode 仍只镜像同一份正式 Lite，不同步源码。

发布时逐项核对：

| 项目 | 同步内容 / 放行条件 |
|---|---|
| 客户端版本 | `voxgo/app_info.py`、`installer/VoxGo.iss`、`scripts/build_portable.ps1`、发布工作流默认版本已为0.6.0；2026-10-30本地Lite已包含多语言展示、单隐私开关、语言计数及精简隐私气泡，尚未公开发布；见[最新交付记录](testing/v0.6.0-today-classifications-2026-10-30.md) |
| GitHub Release | 正式授权后创建实际 `v0.6.0` Release；双语正文来自 `docs/releases/v0.6.0.md`，发布时去掉待发布状态，保留Beta与离线边界 |
| 官网首页（中/英） | 核对五语言文案、语言表、FAQ、description/OG；去掉临时的“当前公开下载v0.5.2 / v0.6.0待发布”说明，替换下载版本文字 |
| GitHub下载 | 仅链接真实存在、已校验的 `releases/download/v0.6.0/` 附件；不能只把全部旧URL字符串替换成0.6.0 |
| 仅发布Lite时 | 本次按四类附件发布，旧Full更新及CUDA下载有对应资源；将来若改为“仅Lite发布”，仍需另行适配更新与下载。官网不应把Full/GPU按钮改成不存在的0.6.0文件；移除这些新版本入口或清楚保留为旧版入口 |
| GitCode镜像 | Lite附件上传并从固定下载URL回读校验后再切换；未完成时保留明确的旧版标注，不能假定同版本镜像存在 |
| 更新元数据 | `docs/update.json` 的 `latest/channel/title`、`release_url`、`notes/notes_zh/notes_en`、各实际附件URL和SHA256须一致；旧Full客户端按edition选择更新，缺失变体不能用0.5.2 ZIP冒充0.6.0。先确认缺失变体的更新行为，再放行清单 |
| README | 中英文同步；去掉顶部“当前公开0.5.2、0.6.0待发布”过渡说明。保留Beta、隐私、安装/模型下载、升级、徽章和社区链接 |
| 静态更新日志与SEO | 实际Release存在后再运行下方生成流程；生成 `docs/changelog/v0.6.0/`、首页Latest摘要和sitemap。发布前只有Markdown草稿，不伪造正式版本页或发布日期 |
| Full遥测兼容 | 原63指标口径不变，语言计数增加协商后的schema3扩展，统一原详细统计开关。2026-10-30生产0006/0007及兼容Worker已启用，已只读核验真实客户端ACK/分类入库；独立今日分类视图已上线，登录后显示待用户刷新确认。Full指统计类别，Lite也受同一规则控制 |

验证真实下载、SHA256、更新清单和中英文网站后，再声明上线完成。此清单不是 push、tag、迁移或部署授权。

## 官网静态更新日志（v2 草案）

### 五语言官网与SEO维护

官网首页为中文`/`、英文`/en/`、日文`/ja/`、韩文`/ko/`、俄文`/ru/`。中英文首页手工维护，日/韩/俄静态HTML由英文首页及`scripts/website_locales/messages.json`生成；各语言标题、description、精简keywords和分享卡片信息来自`metadata.json`。不要单独编辑生成的三个HTML文件。原始字幕示例仍保留英中原文，历史详细更新日志和待发布说明仍为中英文，并在新语言入口标注。

```powershell
# 仅本地生成/校验，不请求翻译服务，也不部署。
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/build_localized_website.py --write --lastmod 2026-10-29
.\.venv-win\Scripts\python.exe -B -X utf8 scripts/build_localized_website.py --check
.\.venv-win\Scripts\python.exe -B -X utf8 -m unittest discover -s tests -p test_website_localization.py -v
```

`--lastmod`应使用首页实际修改日期；省略时保留已有日期，不改变历史Release日期。更改英文文案后需补齐三语词条；未知文案会使构建报错，不默默生成混合语言页面。版本号和日期参数独立保留，GitCode旧镜像的版本不会随GitHub链接一起被提前提升。

正式发布流程在更新中英文链接后离线生成并检查三语页面，再把五个首页及sitemap一起提交。静态更新日志生成器也会刷新三语首页，并保留五个首页的sitemap入口。新Release正文有新词条时，应在发布前准备翻译；构建失败不会自行调用在线翻译或回退成英文。本次按四类构建附件发布，不采用仅Lite发布路径。

五个首页均有自指canonical、互相完整的`hreflang`和中文根页`x-default`；保持显式语言链接，不按浏览器语言强制重定向。SEO注重各页自然、准确的正文和独立描述，keywords不做重复堆砌，不将其视为Google排名因素。页面实现通过不代表已收录、排名提升或搜索摘要一定采用description。上站后才可做各URL的真实访问、Search Console和分享卡片验收；本轮没有部署或提交收录。

### 静态更新日志生成

`scripts/build_website_changelog.py` 从已经发布的 GitHub Release 正文读取中英文更新条目、发布日期和附件，生成 `docs/changelog/`、首页最新更新摘要和 `docs/sitemap.xml`。GitHub Release 是唯一的版本内容来源，网页在构建后就是完整静态 HTML，不依赖访客浏览器请求 GitHub API。

本地生成示例：`.\.venv-win\Scripts\python.exe scripts/build_website_changelog.py --tags v0.5.1 v0.5.0`。现有更早版本的 Release 正文缺少双语结构，首次生成应明确指定 `--tags`；不指定时会校验全部正式版本，可能因旧版格式失败。首页只显示最新三个已生成版本。匿名 GitHub API 有速率限制；在 CI 中使用 `GITHUB_TOKEN`。生成后检查版本页与 Release 正文、下载链接和 sitemap，再提交官网文件。

发布工作流现已接入完整双语正文及静态更新日志：`scripts/release_metadata.py notes`从版本文档生成Release正文和四类SHA256；Release成功后，`site`验证四个实际附件与哈希再写更新清单、清理过渡文案并同步README。随后生成当前及既有双语版本日志、五语首页和sitemap，一起提交。GitCode只有回读校验通过才切换新镜像链接。

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
