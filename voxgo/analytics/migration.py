"""Atomic, conservative Telemetry v2 installation and consent migration."""
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, date
from pathlib import Path
from .aggregation import CrossProcessLock
from .consent import CONSENT_VERSION

IDENTITY_FIELDS = ('basic_install_seed', 'basic_first_run_date', 'telemetry_v2_migrated', 'telemetry_install_origin')
SOURCES = {'new_install_pending', 'new_install_default', 'migration_allowed', 'migration_denied', 'migration_unknown', 'user_enabled', 'user_disabled'}


def valid_uuid(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def validated_consent(data):
    unknown = dict(telemetry_consent='unknown', telemetry_consent_version=0, telemetry_epoch='')
    if not isinstance(data, dict):
        return unknown
    state, version, epoch = (data.get(k) for k in ('telemetry_consent', 'telemetry_consent_version', 'telemetry_epoch'))
    if state not in ('allowed', 'denied', 'unknown') or type(version) is not int or not 0 <= version <= 1000000:
        return unknown
    if state == 'allowed' and (version != CONSENT_VERSION or not valid_uuid(epoch)):
        return unknown
    if state != 'allowed' and epoch != '':
        return unknown
    return dict(telemetry_consent=state, telemetry_consent_version=version, telemetry_epoch=epoch)


def read_consent_authority(root, fallback):
    path = Path(root) / 'telemetry_consent.json'
    data = fallback
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError):
            data = {}
    result = validated_consent(data)
    source = data.get('full_telemetry_source') if isinstance(data, dict) else None
    # A legacy authority's current state always wins over a stale settings grant.
    if source not in SOURCES:
        fallback_source = fallback.get('full_telemetry_source') if isinstance(fallback, dict) else None
        source = (fallback_source if fallback_source in SOURCES and validated_consent(fallback) == result
                  else 'migration_' + result['telemetry_consent'])
    result['full_telemetry_source'] = source
    return result


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, prefix='.settings-', delete=False) as stream:
            temp = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


@contextmanager
def settings_lock(root):
    deadline = time.monotonic() + .08
    while True:
        lock = CrossProcessLock(Path(root) / '.telemetry-settings.lock')
        if lock.__enter__():
            try:
                yield
            finally:
                lock.__exit__(None, None, None)
            return
        if time.monotonic() >= deadline:
            raise TimeoutError('settings busy')
        time.sleep(.02)


def _read_settings(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        return data if isinstance(data, dict) and isinstance(data.get('app', {}), dict) else {}
    except (ValueError, OSError):
        return {}


def _valid_identity(app):
    if app.get('telemetry_v2_migrated') is not True or not valid_uuid(app.get('basic_install_seed')):
        return False
    origin = app.get('telemetry_install_origin')
    first = app.get('basic_first_run_date')
    if origin == 'historical_install':
        return first == ''
    try:
        return origin == 'new_install' and isinstance(first, str) and date.fromisoformat(first).isoformat() == first
    except (ValueError, TypeError):
        return False


def initialize_telemetry_v2(config, runtime_dir, now=None):
    root = Path(runtime_dir)
    try:
        with settings_lock(root):
            path = root / 'user_settings.json'
            existed = path.exists()
            data = _read_settings(path)
            app = data.get('app', {})
            authority = read_consent_authority(root, app)
            if not _valid_identity(app):
                if (app.get('telemetry_v2_migrated', False) is not False
                        or app.get('basic_install_seed', '') != ''
                        or app.get('basic_first_run_date', '') != ''):
                    raise ValueError('existing v2 identity invalid; refusing identity reset')
                historical = existed or (root / 'telemetry_consent.json').exists() or config.app.setup_completed or config.app.telemetry_consent != 'unknown' or getattr(config.app, '_telemetry_existing_config', False) or any((root / p).exists() for p in ('analytics', 'analytics-remote'))
                origin = 'historical_install' if historical else 'new_install'
                if not historical:
                    from voxgo.i18n import system_ui_language
                    config.app.language = system_ui_language()
                app.update(basic_install_seed=str(uuid.uuid4()), basic_first_run_date='' if historical else (now or datetime.now(timezone.utc)).date().isoformat(), telemetry_v2_migrated=True, telemetry_install_origin=origin)
                authority['full_telemetry_source'] = 'migration_' + authority['telemetry_consent'] if historical else 'new_install_pending'
                from voxgo.config.loader import serialize_user_settings
                defaults = serialize_user_settings(config)
                for section, values in defaults.items():
                    data.setdefault(section, values)
                complete_app = dict(defaults['app'])
                complete_app.update(app)
                app = complete_app
                saved_setup = app.get('setup_completed')
                app['setup_completed'] = saved_setup if type(saved_setup) is bool else bool(config.app.setup_completed)
                app.update(authority)
                data['app'] = app
                # Identity becomes usable only after the atomic durable write succeeds.
                atomic_json(path, data)
            if not (root / 'telemetry_consent.json').exists():
                atomic_json(root / 'telemetry_consent.json', authority)
            if type(app.get('setup_completed')) is bool:
                config.app.setup_completed = app['setup_completed']
            if isinstance(app.get('language'), str):
                from voxgo.i18n import normalize_ui_language
                config.app.language = normalize_ui_language(app['language'])
            for key in IDENTITY_FIELDS:
                setattr(config.app, key, app[key])
            for key, value in authority.items():
                setattr(config.app, key, value)
    except (OSError, ValueError, TypeError, KeyError, TimeoutError):
        config.app.basic_install_seed = ''
        config.app.telemetry_v2_migrated = False
        config.app.telemetry_consent = 'unknown'
        config.app.telemetry_epoch = ''
    return config.app


def persist_user_settings(config, root, data):
    with settings_lock(root):
        path = root / 'user_settings.json'
        current = _read_settings(path).get('app', {})
        if _valid_identity(current):
            for key in IDENTITY_FIELDS:
                data['app'][key] = current[key]
                setattr(config.app, key, current[key])
        elif any(current.get(key) not in ('', False, None) for key in IDENTITY_FIELDS[:3]):
            # Ordinary settings saves must not erase evidence of an invalid identity.
            for key in IDENTITY_FIELDS:
                if key in current:
                    data['app'][key] = current[key]
        if getattr(config.app, '_telemetry_consent_changed', False):
            authority = validated_consent(data['app'])
            authority['full_telemetry_source'] = data['app'].get('full_telemetry_source', 'migration_unknown')
            atomic_json(root / 'telemetry_consent.json', authority)
            config.app._telemetry_consent_changed = False
        else:
            authority = read_consent_authority(root, data['app'])
        data['app'].update(authority)
        for key, value in authority.items():
            setattr(config.app, key, value)
        atomic_json(path, data)
