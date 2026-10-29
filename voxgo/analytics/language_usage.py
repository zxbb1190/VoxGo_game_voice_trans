"""Bounded numeric direction summaries. No text, provider URL or UI labels."""
from voxgo.languages import ONLINE_DIRECTIONS, LOCAL_DIRECTIONS, normalize_language_code

LANGUAGE_USAGE_CONSENT_VERSION = 1
LANGUAGE_MODES = ('api', 'offline', 'cache', 'unknown')
MAX_ROWS = 80
MAX_COUNT = 10_000_000
ROW_FIELDS = {'source_lang', 'target_lang', 'mode', 'success', 'failed'}


def language_usage_allowed(config):
    from .consent import may_upload
    return (may_upload(config, True)
            and type(getattr(config, 'telemetry_language_usage_consent_version', 0)) is int
            and getattr(config, 'telemetry_language_usage_consent_version', 0) == LANGUAGE_USAGE_CONSENT_VERSION)


def direction_key(source, target, mode):
    source, target = normalize_language_code(source), normalize_language_code(target)
    if ((source, target) not in ONLINE_DIRECTIONS or mode not in LANGUAGE_MODES
            or (mode == 'offline' and (source, target) not in LOCAL_DIRECTIONS)):
        return None
    return f'{source}>{target}/{mode}'


def usage_map(rows):
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError('invalid language usage')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_FIELDS:
            raise ValueError('invalid language usage row')
        key = direction_key(row['source_lang'], row['target_lang'], row['mode'])
        if (not key or row['source_lang'] != normalize_language_code(row['source_lang'])
                or row['target_lang'] != normalize_language_code(row['target_lang']) or key in result):
            raise ValueError('invalid language direction')
        if any(type(row[name]) is not int or not 0 <= row[name] <= MAX_COUNT for name in ('success', 'failed')):
            raise ValueError('invalid language count')
        if not row['success'] + row['failed']:
            raise ValueError('empty language row')
        result[key] = {name: row[name] for name in ('success', 'failed')}
    return result


def usage_rows(values):
    rows = []
    for key, counts in sorted(values.items()):
        direction, mode = key.split('/')
        source, target = direction.split('>')
        rows.append(dict(source_lang=source, target_lang=target, mode=mode, **counts))
    usage_map(rows)
    return rows


def validate_totals(rows, metrics):
    values = usage_map(rows)
    for result in ('success', 'failed'):
        total = sum(row[result] for row in values.values())
        if total > metrics.get('translation_' + result, 0):
            raise ValueError('language count exceeds total')
        for mode in ('api', 'offline'):
            subtotal = sum(row[result] for key, row in values.items() if key.endswith('/' + mode))
            if subtotal > metrics.get(mode + '_translation_' + result, 0):
                raise ValueError('language count exceeds mode')
        unclassified_mode = sum(row[result] for key, row in values.items()
                                if key.endswith(('/cache', '/unknown')))
        remainder = (metrics.get('translation_' + result, 0)
                     - metrics.get('api_translation_' + result, 0)
                     - metrics.get('offline_translation_' + result, 0))
        if unclassified_mode > remainder:
            raise ValueError('language cache count exceeds remainder')
    return values
