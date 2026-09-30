"""Read-only checks for a VoxGo release candidate."""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


BENCHMARK_ONLY_REQUIREMENTS = {
    "datasets", "evaluate", "jiwer", "librosa", "matplotlib", "pandas",
    "scipy", "soundfile", "torch", "torchaudio", "torchvision",
}
BENCHMARK_PATHS = (
    "data/asr_benchmark", "data/asr-benchmark", "diagnostics",
    "docs/evaluations", "tests/", "scripts/",
)
DEFAULT_CONFIG_PATHS = {
    "audio.latency_mode": "fast",
    "whisper.model_size": "small",
    "whisper.fast_model_size": "base",
    "whisper.english_model_size": "small.en",
    "whisper.fast_english_model_size": "base.en",
    "whisper.pure_english_environment": False,
    "whisper.enable_english_model": False,
    "whisper.device": "cpu",
    "whisper.compute_type": "int8",
    "whisper.auto_cpu_threads": False,
    "whisper.cpu_threads": 2,
    "whisper.num_workers": 1,
    "whisper.beam_size": 1,
    "whisper.condition_on_previous_text": False,
    "whisper.prompt_profile": "none",
    "whisper.initial_prompt": "",
}


class PreflightError(RuntimeError):
    pass


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8-sig")


def _git_show(root: Path, ref: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative}"], cwd=root,
        text=True, encoding="utf-8", errors="replace", capture_output=True,
    )
    if result.returncode:
        raise PreflightError(f"Cannot read {relative} from {ref}: {result.stderr.strip()}")
    return result.stdout


def _dotted_value(document: dict, path: str):
    value = document
    for part in path.split("."):
        value = value[part]
    return value


def parse_requirement_names(text: str) -> set[str]:
    names = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(("-", ".")):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)(?:\[[^]]+\])?", line)
        if match:
            names.add(re.sub(r"[-_.]+", "-", match.group(1)).lower())
    return names


def _static_ast_value(node: ast.AST, constants: dict[str, object]):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in constants:
        return constants[node.id]
    if isinstance(node, ast.Dict):
        return {
            _static_ast_value(key, constants): _static_ast_value(value, constants)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_static_ast_value(item, constants) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(values)
        if isinstance(node, ast.Set):
            return set(values)
        return values
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_static_ast_value(node.operand, constants)
    # Keep expressions such as pyaudio.paInt16 comparable without importing
    # production modules or executing a PyInstaller spec.
    return ast.dump(node, include_attributes=False)


def _module_constants(tree: ast.Module) -> dict[str, object]:
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            value = _static_ast_value(node.value, constants)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = value
    return constants


def _class_defaults(source: str, class_name: str, fields: set[str] | None = None) -> dict:
    tree = ast.parse(source)
    constants = _module_constants(tree)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            values = {}
            for member in node.body:
                if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                    if (fields is None or member.target.id in fields) and member.value is not None:
                        values[member.target.id] = _static_ast_value(member.value, constants)
            return values
    raise PreflightError(f"Cannot find {class_name} defaults")


def _module_assignment(source: str, name: str):
    tree = ast.parse(source)
    constants = _module_constants(tree)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return _static_ast_value(node.value, constants)
    raise PreflightError(f"Cannot find literal assignment {name}")


def check_version_plumbing(root: Path, version: str) -> list[str]:
    checks = {
        "voxgo/app_info.py": (r'^APP_VERSION\s*=\s*["\']([^"\']+)', "APP_VERSION"),
        "scripts/build_portable.ps1": (r'^\s*\[string\]\$Version\s*=\s*["\']([^"\']+)', "build default"),
        "installer/VoxGo.iss": (r'^#define MyAppVersion\s+["\']([^"\']+)', "installer version"),
    }
    messages = []
    for relative, (pattern, label) in checks.items():
        found = re.search(pattern, _read(root, relative), re.MULTILINE)
        if not found or found.group(1) != version:
            raise PreflightError(f"{label} in {relative} must equal {version}")
        messages.append(f"{label}: {version}")

    workflow = _read(root, ".github/workflows/publish-release.yml")
    for pattern in (
        r'description:\s*["\']Release version, for example ([0-9.]+)',
        r'default:\s*["\']([0-9.]+)',
    ):
        found = re.search(pattern, workflow)
        if not found or found.group(1) != version:
            raise PreflightError(f"workflow_dispatch version must equal {version}")
    messages.append(f"workflow_dispatch: {version}")
    return messages


def check_release_notes(root: Path, version: str) -> str:
    relative = f"docs/releases/v{version}.md"
    notes = _read(root, relative)
    required = (
        f"# VoxGo v{version}",
        "## 更新内容",
        "## What's new",
        f'.\\scripts\\build_portable.ps1 -Version "{version}"',
        f"git tag v{version}",
        f"git push origin v{version}",
    )
    missing = [item for item in required if item not in notes]
    if missing:
        raise PreflightError(f"{relative} is missing required release notes/build instructions: {missing}")
    return f"Bilingual release notes and build/publish commands: {relative}"


def check_community_links(root: Path) -> list[str]:
    source = _read(root, "voxgo/app_info.py")
    constants = {}
    for key in ("KOOK_URL", "DISCORD_URL"):
        match = re.search(rf'^{key}\s*=\s*["\']([^"\']+)', source, re.MULTILINE)
        if not match:
            raise PreflightError(f"Missing {key}")
        constants[key] = match.group(1)
        parsed = urlsplit(match.group(1))
        allowed_hosts = {
            "KOOK_URL": {"kook.vip"},
            "DISCORD_URL": {"discord.gg"},
        }[key]
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts or not parsed.path.strip("/"):
            raise PreflightError(f"{key} is not a configured HTTPS invitation URL")

    expected = {
        "KOOK_URL": "https://kook.vip/hr0hMS",
        "DISCORD_URL": "https://discord.gg/mtnFmUJJ4y",
    }
    if constants != expected:
        raise PreflightError(f"Community invitations differ from confirmed project URLs: {constants}")
    for page in ("docs/index.html", "docs/en/index.html"):
        html = _read(root, page)
        if any(url not in html for url in constants.values()):
            raise PreflightError(f"{page} must retain the configured KOOK and Discord invitations")
    return [f"{key}: {value}" for key, value in constants.items()]


def check_product_defaults(root: Path, base_ref: str) -> list[str]:
    current_json = json.loads(_read(root, "config.example.json"))
    base_json = json.loads(_git_show(root, base_ref, "config.example.json"))
    for path, expected in DEFAULT_CONFIG_PATHS.items():
        current_value = _dotted_value(current_json, path)
        base_value = _dotted_value(base_json, path)
        if current_value != base_value:
            raise PreflightError(f"Product default changed from {base_ref}: {path}")
        if current_value != expected:
            raise PreflightError(f"Unexpected release default for {path}: {current_value!r}")

    class_checks = {
        "voxgo/audio/capture.py": {"AudioConfig": None},
        "voxgo/ui/config_models.py": {
            "AudioDeviceConfig": None,
            "WhisperDeviceConfig": None,
        },
        "voxgo/asr/whisper_engine.py": {"WhisperConfig": None},
    }
    for relative, classes in class_checks.items():
        current_source = _read(root, relative)
        base_source = _git_show(root, base_ref, relative)
        for class_name, fields in classes.items():
            current_defaults = _class_defaults(current_source, class_name, fields)
            base_defaults = _class_defaults(base_source, class_name, fields)
            if current_defaults != base_defaults:
                raise PreflightError(f"{class_name} product defaults changed from {base_ref}")

    current_audio = _module_assignment(_read(root, "voxgo/audio/capture.py"), "AUDIO_LATENCY_PRESETS")
    base_audio = _module_assignment(_git_show(root, base_ref, "voxgo/audio/capture.py"), "AUDIO_LATENCY_PRESETS")
    current_english = _module_assignment(_read(root, "voxgo/audio/capture.py"), "ENGLISH_AUDIO_LATENCY_BIAS")
    base_english = _module_assignment(_git_show(root, base_ref, "voxgo/audio/capture.py"), "ENGLISH_AUDIO_LATENCY_BIAS")
    if current_audio != base_audio or current_english != base_english:
        raise PreflightError(f"Audio latency preset values changed from {base_ref}")

    whisper_source = _read(root, "voxgo/asr/whisper_engine.py")
    if not re.search(r'"none"\s*:\s*None', whisper_source):
        raise PreflightError("The none prompt profile must remain empty")
    if not re.search(
        r'if\s+profile\s*==\s*["\']game["\']\s+and\s+'
        r'self\._effective_model_size\(\)\.lower\(\)\.endswith\(["\']\.en["\']\)',
        whisper_source,
    ):
        raise PreflightError("Expected the existing game prompt condition for .en models")
    return [
        f"config.example.json defaults unchanged from {base_ref}",
        "Audio/Whisper dataclass defaults unchanged",
        "Audio latency preset values unchanged",
        "prompt_profile=none; existing game prompt .en conditional present",
    ]


def audit_packaging_inputs(spec_source: str, build_script: str) -> list[str]:
    spec_tree = ast.parse(spec_source)
    excludes = _module_assignment(spec_source, "excludes")
    missing_excludes = {"tests", "diagnostics", "scripts"} - set(excludes)
    if missing_excludes:
        raise PreflightError(f"PyInstaller exclusions missing: {sorted(missing_excludes)}")

    data_nodes = []
    for node in spec_tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "datas" for target in node.targets
        ):
            data_nodes.extend(ast.walk(node.value))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "append" and call.args:
                data_nodes.extend(ast.walk(call.args[0]))
    data_strings = [node.value.lower().replace("\\", "/") for node in data_nodes
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    for source in data_strings:
        if any(fragment in source for fragment in BENCHMARK_PATHS):
            raise PreflightError(f"Benchmark/test material is bundled as data: {source}")

    if not re.search(r'Copy-Item\s+-Recurse\s+["\']dist[\\/]VoxGo["\']', build_script, re.IGNORECASE):
        raise PreflightError("Portable archive must be assembled from dist/VoxGo only")
    if not re.search(r'Compress-DirectoryWithRetry\s+-SourceDir\s+\$packageDir', build_script):
        raise PreflightError("Portable archive source directory is not the staged PyInstaller output")
    return [
        "PyInstaller excludes tests, diagnostics, and scripts; no benchmark data/report inputs",
        "Portable archives contain only the staged dist/VoxGo output",
    ]


def check_benchmark_and_packaging(root: Path, base_ref: str) -> list[str]:
    requirements = _read(root, "requirements.txt")
    baseline = _git_show(root, base_ref, "requirements.txt")
    current_names = parse_requirement_names(requirements)
    baseline_names = parse_requirement_names(baseline)
    added = current_names - baseline_names
    benchmark_deps = current_names & BENCHMARK_ONLY_REQUIREMENTS
    if added:
        raise PreflightError(f"New application requirements versus {base_ref}: {sorted(added)}")
    if benchmark_deps:
        raise PreflightError(f"Benchmark-only packages are application requirements: {sorted(benchmark_deps)}")
    packaging_results = audit_packaging_inputs(
        _read(root, "VoxGo.spec"), _read(root, "scripts/build_portable.ps1")
    )
    return [
        "No new requirements; no benchmark-only requirement",
        *packaging_results,
    ]


def validate_update_manifest(current_text: str, baseline_text: str, version: str, base_ref: str) -> str:
    current = json.loads(current_text)
    baseline = json.loads(baseline_text)
    if current != baseline:
        raise PreflightError(f"docs/update.json changed from {base_ref}; preserve published metadata before release")
    if current.get("latest") == version:
        raise PreflightError(
            f"docs/update.json already points to {version}; verify published assets before advancing it"
        )
    return f"docs/update.json matches {base_ref} at published version {current.get('latest')}"


def run_preflight(root: Path, version: str, base_ref: str = "origin/main") -> list[str]:
    results = []
    results.extend(check_version_plumbing(root, version))
    results.append(check_release_notes(root, version))
    results.extend(check_community_links(root))
    results.extend(check_product_defaults(root, base_ref))
    results.extend(check_benchmark_and_packaging(root, base_ref))
    results.append(validate_update_manifest(
        _read(root, "docs/update.json"),
        _git_show(root, base_ref, "docs/update.json"),
        version,
        base_ref,
    ))
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version without the leading v")
    parser.add_argument("--base-ref", default="origin/main", help="Published baseline for default/dependency checks")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        parser.error("--version must use MAJOR.MINOR.PATCH, for example 0.5.2")
    try:
        results = run_preflight(args.root.resolve(), args.version, args.base_ref)
    except (PreflightError, OSError, ValueError, KeyError, SyntaxError) as exc:
        print(f"RELEASE PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"Release preflight passed for v{args.version} (baseline {args.base_ref})")
    for result in results:
        print(f"  PASS  {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
