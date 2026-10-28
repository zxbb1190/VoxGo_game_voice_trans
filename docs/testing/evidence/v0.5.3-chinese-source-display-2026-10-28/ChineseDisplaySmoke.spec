# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator/build/chinese-display-20261028/frozen_smoke.py'],
    pathex=['C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator'],
    binaries=[],
    datas=[('C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator/voxgo/ui/_opencc/config', 'voxgo/ui/_opencc/config'), ('C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator/voxgo/ui/_opencc/dictionary', 'voxgo/ui/_opencc/dictionary'), ('C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator/voxgo/ui/_opencc/LICENSE.txt', 'voxgo/ui/_opencc'), ('C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator/voxgo/ui/_opencc/NOTICE.txt', 'voxgo/ui/_opencc'), ('C:\\Users\\Administrator\\.codex\\worktrees\\multilingual-online-053\\game_voice_translator/voxgo/ui/_opencc/UPSTREAM.json', 'voxgo/ui/_opencc')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChineseDisplaySmoke',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChineseDisplaySmoke',
)
