"""Build-provided edition; never infer an edition from a directory name."""
import json
import sys
from pathlib import Path


def package_type():
    if not getattr(sys, 'frozen', False):
        return 'source'
    try:
        path = Path(__file__).resolve().parent.parent / 'package-info.json'
        if path.stat().st_size > 1024:
            return 'unknown'
        value = json.loads(path.read_text(encoding='utf-8')).get('package_type')
        return value if value in ('lite', 'full', 'full-cuda') else 'unknown'
    except (OSError, ValueError, AttributeError):
        return 'unknown'
