"""Fail-closed authorization for remote usage statistics."""
CONSENT_VERSION = 3


def telemetry_title(english=False):
    return 'Help improve VoxGo' if english else '帮助 VoxGo 改进体验'


def telemetry_summary(english=False):
    if english:
        return ('Basic statistics are always enabled to count daily active installations, using a daily identifier that is not linked across days. '
                'Optional Full statistics help improve usage and stability; you can turn Full off at any time. '
                'Neither includes audio, recognized text or translations.')
    return ('基础统计始终启用，用于统计每日活跃安装数，使用不跨日关联的每日标识。'
            '可选的详细使用与稳定性统计帮助改进体验，你可以随时关闭。均不包含语音、识别或翻译内容。')


def normalize_consent(value):
    return value if value in ('unknown', 'allowed', 'denied') else 'unknown'


def may_upload(app_config, remote_enabled=False):
    # Remote configuration can disable collection, never grant user consent.
    if (getattr(app_config, 'telemetry_install_origin', '') == 'new_install'
            and getattr(app_config, 'setup_completed', False) is not True):
        return False
    return (remote_enabled is True
            and getattr(app_config, 'telemetry_consent', 'unknown') == 'allowed'
            and getattr(app_config, 'telemetry_consent_version', 0) == CONSENT_VERSION)
