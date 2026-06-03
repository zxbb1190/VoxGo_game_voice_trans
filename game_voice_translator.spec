# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import json
import shutil
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
root = Path.cwd()
safe_config = root / "build" / "packaged_config" / "config.json"
safe_config.parent.mkdir(parents=True, exist_ok=True)
safe_config.write_text(
    (root / "config.example.json").read_text(encoding="utf-8"),
    encoding="utf-8",
)
safe_models = root / "build" / "packaged_models" / ".models"
shutil.rmtree(safe_models.parent, ignore_errors=True)
safe_models.mkdir(parents=True, exist_ok=True)
cachedir_tag = root / ".models" / "CACHEDIR.TAG"
if cachedir_tag.exists():
    shutil.copy2(cachedir_tag, safe_models / "CACHEDIR.TAG")

config_data = json.loads((root / "config.example.json").read_text(encoding="utf-8"))
model_size = config_data.get("whisper", {}).get("model_size", "small")
model_repo = f"models--Systran--faster-whisper-{model_size}"
source_repo = root / ".models" / model_repo
if not source_repo.exists():
    raise FileNotFoundError(f"Packaged Whisper model cache is missing: {source_repo}")

snapshot = (source_repo / "refs" / "main").read_text(encoding="utf-8").strip()
safe_repo = safe_models / model_repo
(safe_repo / "refs").mkdir(parents=True, exist_ok=True)
(safe_repo / "snapshots" / snapshot).mkdir(parents=True, exist_ok=True)
shutil.copy2(source_repo / "refs" / "main", safe_repo / "refs" / "main")
for source in (source_repo / "snapshots" / snapshot).iterdir():
    if source.is_file() or source.is_symlink():
        shutil.copy2(
            source,
            safe_repo / "snapshots" / snapshot / source.name,
            follow_symlinks=True,
        )

datas = [
    (str(safe_config), "."),
    (str(safe_models), ".models"),
    (str(root / ".venv-win" / "Lib" / "site-packages" / "faster_whisper" / "assets"), "faster_whisper/assets"),
]

site_packages = root / ".venv-win" / "Lib" / "site-packages"
system32 = Path("C:/Windows/System32")
binaries = [
    (str(site_packages / "ctranslate2" / "cudnn64_9.dll"), "ctranslate2"),
    (str(system32 / "msvcp140.dll"), "PyQt5/Qt5/bin"),
    (str(system32 / "msvcp140_1.dll"), "PyQt5/Qt5/bin"),
    (str(system32 / "msvcp140_2.dll"), "PyQt5/Qt5/bin"),
]

hiddenimports = [
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "websockets.legacy",
    "websockets.legacy.server",
    "qrcode",
    "PIL.Image",
    "librosa",
    "soxr",
    "soundfile",
]
hiddenimports += collect_submodules("setuptools._vendor.backports")

excludes = [
    "pytest",
    "matplotlib",
    "IPython",
    "notebook",
    "torch",
    "torchaudio",
    "torchvision",
    "tensorflow",
    "tensorboard",
    "sklearn",
    "pandas",
]

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GameVoiceTranslator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GameVoiceTranslator",
)
