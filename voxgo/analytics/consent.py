"""Fail-closed authorization for remote usage statistics."""
CONSENT_VERSION = 3


def telemetry_title(english=False):
    return 'Help improve VoxGo' if english else '帮助 VoxGo 改进体验'


def telemetry_summary(english=False, confirmation=False):
    if english:
        return (
            'Would you like to send usage and stability statistics to help improve VoxGo?\n'
            'Audio, recognized text and translations are not included. You can turn this off in Settings at any time.'
            if confirmation else
            'Send usage and stability statistics to help us improve features and performance. '
            'Audio, recognized text and translations are not included. You can turn this off at any time.'
        )
    return (
        '是否愿意发送使用情况和运行稳定性统计，帮助我们改进 VoxGo？\n'
        '不包含语音、识别或翻译内容，你可以随时在设置中关闭。'
        if confirmation else
        '发送使用情况和运行稳定性统计，帮助我们优化功能与性能。不包含语音、识别或翻译内容，你可以随时关闭。'
    )


def normalize_consent(value):
    return value if value in ('unknown', 'allowed', 'denied') else 'unknown'


def may_upload(app_config, remote_enabled=False):
    # Remote configuration can disable collection, never grant user consent.
    return (remote_enabled is True
            and getattr(app_config, 'telemetry_consent', 'unknown') == 'allowed'
            and getattr(app_config, 'telemetry_consent_version', 0) == CONSENT_VERSION)


def privacy_text(english=False):
    if english:
        return (
            'Remote usage statistics are off by default. With your explicit permission, VoxGo sends '
            'only post-consent daily aggregates to https://api.voxgo.cn (Cloudflare). A random installation identifier '
            'links daily aggregates; it is not a hardware identifier. The service sees your network IP address. '
            'Remote reporting also requires an enabled service configuration.\n\n'
            'Statistics cover application version and package edition, translation mode, success/failure counts, '
            'performance, clean shutdown counts and starts that discover a previous unclean shutdown. '
            'No crash stack or error message is uploaded. '
            'They exclude audio, recognized text, translations, API keys, file paths and hardware identifiers.\n\n'
            'Local statistics are stored separately on this computer, retained for up to 30 days '
            '(90 files / 2 MiB maximum). Declining remote reporting does not disable local statistics.\n\n'
            'The remote upload buffer covers the latest 7 UTC dates. Server retention targets 30 days '
            'with scheduled server cleanup; actual deletion depends on successful cleanup runs. You may withdraw consent here '
            'at any time. Re-enabling starts a new identifier and does not backfill pre-consent data. '
            'Withdrawal stops future reporting, but cannot recall '
            'a request already sent. A change in the scope of collection will require new consent.\n\n'
            'Translation providers and update/model downloads make their own network requests. '
            'Debug logs are separate and may contain text; review them before sharing. '
            'Feedback is shared only when you copy or submit it yourself.'
        )
    return (
        '远程使用统计默认关闭。明确授权后，仅将授权后产生的每日汇总发送至 https://api.voxgo.cn（Cloudflare）。使用随机安装标识关联每日数据，不使用硬件标识；接收服务可见网络 IP。远程配置允许时才会上报。\n\n'
        '统计范围：应用版本与安装包类型、翻译模式、成功与失败数量、性能、正常退出次数、启动时发现上次未正常退出的次数。不上传崩溃堆栈或错误正文；不包含语音、识别原文、译文、API Key、本地路径或硬件标识。\n\n'
        '本地统计单独保存在此电脑，最多保留 30 天、90 个文件、总量 2 MiB。拒绝远程统计不会关闭本地统计。\n\n'
        '远程待上传缓冲仅覆盖最近 7 个 UTC 日期。服务端目标保留期为 30 天，通过服务端定时任务清理；实际删除取决于清理任务成功运行。可随时撤回授权，停止后续发送；已发出的请求无法撤回。再次授权使用新标识，不补传授权前数据。采集范围变更需要重新授权。\n\n'
        '翻译服务、更新检查及模型下载有各自的网络请求。调试日志独立于统计，可能包含文本，分享前请检查。'
        '反馈信息仅在你主动复制或提交时分享。'
    )
