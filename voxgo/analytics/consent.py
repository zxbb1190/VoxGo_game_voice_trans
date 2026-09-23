"""Fail-closed authorization for remote usage statistics."""
CONSENT_VERSION = 3


def telemetry_title(english=False):
    return 'Help improve VoxGo' if english else '帮助 VoxGo 改进体验'


def telemetry_summary(english=False, confirmation=False):
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


def privacy_text(english=False):
    if english:
        return (
            'Basic statistics are always enabled to count daily active installations. They include application version, '
            'package edition, whether this UTC date is the installation first-run day, setup completion, and the Full '
            'statistics state and its source. A daily identifier is not linked across dates. This is de-identified '
            'installation measurement, not a count of people. The receiving service sees the network IP, but does not store it in D1.\n\n'
            'Full usage and stability statistics follow your setup or Settings choice. New installations default to '
            'checked in the setup wizard, but Full starts only after setup is completed. Historical allowed, denied '
            'and unknown choices are preserved. Full includes application version, package edition, translation mode, '
            'success/failure counts, active use duration, ASR/translation performance and clean/unclean shutdown counts. '
            'It uses a random installation identifier across days. No audio, recognized text, translations, keys, '
            'paths, hardware identifiers, crash stacks or error messages are uploaded by either channel.\n\n'
            'You may disable Full in Settings. This stops future Full reporting, but does not disable Basic or local '
            'statistics and cannot recall an already sent request. Re-enabling Full starts a new identifier without '
            'backfilling disabled-period data. New data categories require new authorization; consent version remains 3 '
            'for refinements of existing numeric statistics.\n\n'
            'Local statistics retain up to 30 days within 90 files / 2 MiB. Remote buffers cover up to 7 UTC dates. '
            'Server retention targets 30 days and depends on scheduled cleanup. Translation, model downloads and updates '
            'make their own requests. Debug logs are separate and may contain text; review them before sharing. '
            'Feedback is shared only when you copy or submit it.'
        )
    return (
        '基础统计始终启用，用于统计每日活跃安装数。包含应用版本、安装包类型、当天是否为首次启动日、'
        '配置是否完成、详细统计开关及来源。使用不跨日关联的每日标识，是去标识化的安装统计，不代表自然人数。'
        '接收服务可见网络 IP，但不将 IP 存入 D1。\n\n'
        '详细使用与稳定性统计遵循首次向导或设置中的选择。新安装向导默认勾选，完成向导后才启用；'
        '历史开启、拒绝和未知状态保持原选择。包含版本、安装包类型、翻译模式、成功失败数量、活跃使用时长、'
        '识别与翻译性能、正常退出与未正常退出次数，使用随机安装标识关联每日汇总。'
        '两类统计均不上传语音、识别或翻译内容、密钥、本地路径、硬件标识、崩溃堆栈或错误正文。\n\n'
        '可以随时在设置中关闭详细统计，停止后续详细统计上报；基础统计和本地统计继续运行。已发出的请求无法撤回。'
        '再次开启详细统计使用新标识，不补传关闭期间数据。新增数据类别需要重新授权；已有数值统计细化保持授权版本 3。\n\n'
        '本地统计最多保留 30 天、90 个文件、总量 2 MiB。远程待上传缓冲覆盖最多 7 个 UTC 日期。'
        '服务端目标保留期为 30 天，实际删除取决于定时清理成功运行。翻译服务、模型下载和更新有各自的网络请求。'
        '调试日志独立于统计，可能含文本，分享前请检查。反馈仅在你主动复制或提交时分享。'
    )
