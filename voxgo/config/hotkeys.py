"""Shared action names and duplicate binding detection for settings and runtime."""
HOTKEY_ACTIONS = (
    ('toggle_overlay', '显示/隐藏', 'Show / Hide'),
    ('clear_history', '清空历史', 'Clear Subtitles'),
    ('toggle_translation', '暂停/恢复', 'Pause / Resume'),
    ('toggle_lock', '锁定/解锁', 'Lock / Unlock'),
    ('toggle_compact', '紧凑模式', 'Compact Mode'),
    ('toggle_display_mode', '切换字幕模式', 'Switch subtitle mode'),
)


def canonical_hotkey(value):
    aliases = {'control': 'ctrl', 'windows': 'win', 'super': 'win', 'return': 'enter', 'escape': 'esc'}
    value = str(value or '').strip().lower()
    if not value:
        return ()
    return tuple(tuple(sorted(aliases.get(key.strip(), key.strip()) for key in step.split('+')))
                 for step in value.split(','))


def hotkey_conflicts(config):
    seen, conflicts = {}, []
    for name, _, _ in HOTKEY_ACTIONS:
        value = canonical_hotkey(getattr(config, name, ''))
        if not value:
            continue
        if value in seen:
            conflicts.append((seen[value], name))
        else:
            seen[value] = name
    return conflicts
