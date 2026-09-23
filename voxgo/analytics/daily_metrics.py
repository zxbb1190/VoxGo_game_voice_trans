"""One shared collector per process; events never perform disk writes."""
import math
import threading
from copy import deepcopy

COUNTERS = {'app_starts', 'sessions', 'session_seconds', 'offline_sessions',
            'api_sessions', 'translation_success', 'translation_failed',
            'clean_exits', 'unclean_starts'}
V1_COUNTERS = COUNTERS.copy()
COUNTERS |= {mode + '_translation_' + result for mode in ('api', 'offline')
             for result in ('success', 'failed')}
BUCKETS = ('lt_500', '500_1000', '1000_2000', '2000_5000', 'ge_5000')
LATENCIES = {'asr_latency', 'translation_latency'}
METRICS = COUNTERS | {n + s for n in LATENCIES for s in ('_sum_ms', '_samples')}
V1_METRICS = V1_COUNTERS | {n + s for n in LATENCIES for s in ('_sum_ms', '_samples')}
METRICS |= {n + '_' + bucket for n in LATENCIES for bucket in BUCKETS}
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
        valid = (data.get('schema_version') in (1, 2) and data.get('date') == day
                 and isinstance(metrics, dict))
        clean = {k: v for k, v in metrics.items()
                 if k in METRICS and type(v) is int and 0 <= v <= LIMIT} if valid else {}
        return {'schema_version': 2, 'date': day, 'app_version': self.app_version,
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

    @staticmethod
    def _valid_elapsed(elapsed_ms):
        return (type(elapsed_ms) in (int, float) and math.isfinite(elapsed_ms)
                and 0 <= elapsed_ms <= 3600000)

    def _observe_locked(self, prefix, elapsed_ms):
        metrics = self.snapshot['metrics']
        if metrics.get(prefix + '_samples', 0) >= LIMIT:
            return False
        # Bucket original milliseconds, before rounding the accumulated sum.
        bucket = BUCKETS[sum(elapsed_ms >= edge for edge in (500, 1000, 2000, 5000))]
        for suffix, amount in [('_sum_ms', round(elapsed_ms)), ('_samples', 1),
                               ('_' + bucket, 1)]:
            key = prefix + suffix
            metrics[key] = min(LIMIT, metrics.get(key, 0) + amount)
        return True

    def observe(self, name, elapsed_ms):
        prefix = name if name.endswith('_latency') else name + '_latency'
        if prefix not in LATENCIES or not self._valid_elapsed(elapsed_ms):
            return False
        with self._lock:
            self._rollover()
            return self._observe_locked(prefix, elapsed_ms)

    def translation_result(self, success, elapsed_ms=None, mode=None):
        """Apply one result as a single day/lock transaction, or drop it whole."""
        if type(success) is not bool or mode not in (None, 'api', 'offline'):
            return False
        with self._lock:
            self._rollover()
            metrics = self.snapshot['metrics']
            result = 'translation_success' if success else 'translation_failed'
            if metrics.get(result, 0) >= LIMIT:
                return False
            metrics[result] = metrics.get(result, 0) + 1
            if mode is not None:
                key = mode + '_' + result
                metrics[key] = min(LIMIT, metrics.get(key, 0) + 1)
            if self._valid_elapsed(elapsed_ms):
                self._observe_locked('translation_latency', elapsed_ms)
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
