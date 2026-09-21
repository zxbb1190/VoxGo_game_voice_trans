"""One shared collector per process; events never perform disk writes."""
import math
import threading
from copy import deepcopy

COUNTERS = {'app_starts', 'sessions', 'session_seconds', 'offline_sessions',
            'api_sessions', 'translation_success', 'translation_failed',
            'clean_exits', 'unclean_starts'}
LATENCIES = {'asr_latency', 'translation_latency'}
METRICS = COUNTERS | {n + s for n in LATENCIES for s in ('_sum_ms', '_samples')}
LIMIT = 10 ** 12


class DailyMetrics:
    def __init__(self, store, app_version, package_type='unknown', environment=None):
        self.store = store
        self.app_version = app_version
        self.package_type = package_type
        self.environment = {k: str(v)[:100] for k, v in (environment or {}).items()
                            if k in {'asr_model', 'translation_model', 'compute_backend'}}
        self._lock = threading.RLock()
        self.day = store.today().isoformat()
        self.snapshot = self._load(self.day)
        self._pending = {}

    def _load(self, day):
        data = self.store.load(day)
        metrics = data.get('metrics', {})
        valid = (data.get('schema_version') == 1 and data.get('date') == day
                 and isinstance(metrics, dict))
        clean = {k: v for k, v in metrics.items()
                 if k in METRICS and type(v) is int and 0 <= v <= LIMIT} if valid else {}
        return {'schema_version': 1, 'date': day, 'app_version': self.app_version,
                'package_type': self.package_type, 'environment': self.environment.copy(),
                'metrics': clean}

    def _rollover(self):
        today = self.store.today().isoformat()
        if today == self.day:
            return
        self._pending[self.day] = self.snapshot
        self.day = today
        self.snapshot = self._pending.pop(today, None) or self._load(today)
        for day in sorted(self._pending)[:-self.store.retention_days]:
            del self._pending[day]

    def increment(self, name, value=1):
        if name not in COUNTERS or type(value) is not int or not 0 <= value <= LIMIT:
            return False
        with self._lock:
            self._rollover()
            metrics = self.snapshot['metrics']
            metrics[name] = min(LIMIT, metrics.get(name, 0) + value)
        return True

    def observe(self, name, elapsed_ms):
        prefix = name if name.endswith('_latency') else name + '_latency'
        if (prefix not in LATENCIES or type(elapsed_ms) not in (int, float)
                or not math.isfinite(elapsed_ms) or not 0 <= elapsed_ms <= 3600000):
            return False
        with self._lock:
            self._rollover()
            metrics = self.snapshot['metrics']
            for suffix, amount in [('_sum_ms', round(elapsed_ms)), ('_samples', 1)]:
                key = prefix + suffix
                metrics[key] = min(LIMIT, metrics.get(key, 0) + amount)
        return True

    def flush(self):
        with self._lock:
            self._rollover()
            for day, snapshot in list(self._pending.items()):
                if self.store.save(day, snapshot):
                    del self._pending[day]
            return self.store.save(self.day, self.snapshot) and not self._pending

    def snapshot_copy(self):
        with self._lock:
            return deepcopy(self.snapshot)
