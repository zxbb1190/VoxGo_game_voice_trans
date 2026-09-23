# 发布流程

1. 更新 `voxgo/app_info.py`、`installer/VoxGo.iss` 和 `scripts/build_portable.ps1` 的版本号。
2. 在 `.github/workflows/publish-release.yml` 中同步版本示例和发布说明。
3. 发布说明必须同时填写 `notes_zh` 和 `notes_en`；`docs/update.json` 的下载地址、版本号和 SHA256 必须指向同一个 tag。
4. 运行 Windows 全量测试、`git diff --check`，并用 Windows 便携包验证启动、托盘和更新替换。
5. 提交 `main`，创建并推送 `vX.Y.Z` 标签。GitHub Actions 会构建 Lite、Full、Full-CUDA、CUDA runtime，上传 Release 后再更新 `docs/update.json` 和官网链接。
6. 核对 Release 四个附件、SHA256、双语清单和官网部署状态。更新弹窗按用户设置的语言读取对应的 `notes_zh` 或 `notes_en`，不要在弹窗增加语言切换。

更新器会保留配置、Whisper/离线翻译模型和 CUDA 运行库；首次从不支持应用内更新的旧版本升级仍需手动下载。

## 国内 Lite 镜像

- GitCode 镜像目前仅提供 Lite，中文和英文官网的首屏与 Lite 下载卡片均提供入口。
- 地址格式：`https://gitcode.com/zxbb1190/VoxGo/releases/download/vX.Y.Z/VoxGo-vX.Y.Z-lite.zip`。
- 每次发版须将对应版本的正式 Lite ZIP 同步上传到 GitCode 的 `zxbb1190/VoxGo` Release；使用 GitHub 发布的同一文件，核对 SHA256 一致，不单独重新打包。
- 发布工作流更新官网时，会同时替换 GitHub 和 GitCode 下载地址中的标签版本与文件名版本。工作流只更新链接，不负责上传 GitCode 附件；镜像上传和可下载性检查是发版收尾的必做项。
- 官网发布前确认镜像附件已就绪；发布后核对中英文页面的国内入口均可下载当前版本。未提供镜像的 Full、Full-CUDA 和 CUDA runtime 继续使用 GitHub。
- `docs/update.json` 仍保留原有 GitHub 地址，本次官网镜像入口不改变客户端自动更新的下载来源。

- 镜像附件尚未就绪时，官网保留上一版国内地址并明确标注版本；工作流通过可用性和文件大小检查后才升级镜像地址。手动上传后仍须核对 SHA256，并更新中英文官网镜像链接及版本标签。
