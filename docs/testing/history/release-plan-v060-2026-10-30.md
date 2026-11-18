# Historical v0.6.0 release plan

Archived on 2026-11-04. The following plan contains historical status and authorization language; it does not describe current publication state or grant a new release authorization. See [the maintained release procedure](../../release_process.md).

## v0.6.0 多语言展示同步（本次按四附件工作流执行）

产品文案统一为：五语言识别、20个在线翻译方向；日语、韩语、俄语标为 Beta，表示持续优化，并非未开放。离线 OPUS 仍仅英中双向。本次已获发布授权，按现有工作流构建 Lite、Full、Full-CUDA 和 CUDA runtime；实际 Release 及附件校验通过后同步官网、README 和更新清单。GitCode 仍只镜像同一份正式 Lite，不同步源码。

发布时逐项核对：

| 项目 | 同步内容 / 放行条件 |
|---|---|
| 客户端版本 | `voxgo/app_info.py`、`installer/VoxGo.iss`、`scripts/build_portable.ps1`、发布工作流默认版本已为0.6.0；2026-10-30本地Lite已包含多语言展示、单隐私开关、语言计数及精简隐私气泡，尚未公开发布；见[最新交付记录](../v0.6.0-today-classifications-2026-10-30.md) |
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
