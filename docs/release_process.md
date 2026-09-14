# 发布流程

1. 更新 `voxgo/app_info.py`、`installer/VoxGo.iss` 和 `scripts/build_portable.ps1` 的版本号。
2. 在 `.github/workflows/publish-release.yml` 中同步版本示例和发布说明。
3. 发布说明必须同时填写 `notes_zh` 和 `notes_en`；`docs/update.json` 的下载地址、版本号和 SHA256 必须指向同一个 tag。
4. 运行 Windows 全量测试、`git diff --check`，并用 Windows 便携包验证启动、托盘和更新替换。
5. 提交 `main`，创建并推送 `vX.Y.Z` 标签。GitHub Actions 会构建 Lite、Full、Full-CUDA、CUDA runtime，上传 Release 后再更新 `docs/update.json` 和官网链接。
6. 核对 Release 四个附件、SHA256、双语清单和官网部署状态。更新弹窗按用户设置的语言读取对应的 `notes_zh` 或 `notes_en`，不要在弹窗增加语言切换。

更新器会保留配置、Whisper/离线翻译模型和 CUDA 运行库；首次从不支持应用内更新的旧版本升级仍需手动下载。
