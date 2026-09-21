"""Local-only, fixed-size diagnostic status; never contains telemetry payloads."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


class AnalyticsDebug:
    FIELDS = frozenset(('consent', 'consent_version', 'config_enabled', 'sampled',
        'daily_snapshot_exists', 'outbox_count', 'revision', 'next_retry_at',
        'failure_count', 'uploader_started', 'last_attempt', 'last_schedule',
        'last_result', 'skip_reason', 'http_status', 'error_type',
        'config_request_url', 'config_http_status', 'config_server_header',
        'config_cf_ray', 'config_raw_enabled', 'config_effective_enabled', 'config_attempt_at'))

    def __init__(self, root):
        self.root = Path(root)
        self.state = dict.fromkeys(self.FIELDS)
        self._saved = None

    def update(self, persist=True, **values):
        for key, value in values.items():
            if key not in self.FIELDS:
                continue
            if value is None or type(value) in (bool, int, float):
                self.state[key] = value
            elif key == 'config_request_url' and value == 'https://api.voxgo.cn/v1/config':
                self.state[key] = value
            elif key in ('config_server_header', 'config_cf_ray') and type(value) is str:
                if len(value) <= 128 and all(c.isascii() and (c.isalnum() or c in ' ._/-') for c in value):
                    self.state[key] = value
            elif type(value) is str and len(value) <= 64 and all(
                    c.isascii() and (c.isalnum() or c == '_') for c in value):
                self.state[key] = value
        # No directory creation: diagnostics must never resurrect a revoked epoch.
        if not persist or not self.root.is_dir():
            return
        temporary = None
        try:
            data = json.dumps(self.state, sort_keys=True, allow_nan=False)
            if data == self._saved or len(data.encode('utf-8')) > 4096:
                return
            with NamedTemporaryFile('w', encoding='utf-8', dir=self.root,
                                    prefix='.debug-', delete=False) as file:
                temporary = Path(file.name)
                file.write(data)
            os.replace(temporary, self.root / 'debug-state.json')
            self._saved = data
        except Exception:
            pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
