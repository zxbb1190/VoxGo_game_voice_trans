"""Verified portable Windows updates. Preparation never changes the running app.

Call ``prepare_update`` on a worker thread, then ``launch_update`` after the
user accepts installation. Only shut down the application after launch returns.
The detached helper captures the current process handle before acknowledging
readiness, and performs the replacement after that exact process has exited.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import urlparse
import zipfile
from dataclasses import dataclass

from voxgo.update.checker import UpdateInfo

MAX_DOWNLOAD_BYTES = 8 * 1024**3
MAX_EXTRACTED_BYTES = 16 * 1024**3
MAX_ARCHIVE_ENTRIES = 100000
PRESERVE_PATHS = (
    'config.json', '_internal/config.json', 'user_settings.json', '.models', '.translation-models', '.translation_models',
    'models', 'runtime/cuda', '_internal/.models',
    '_internal/.translation_models', '_internal/runtime/cuda',
)


class UpdateInstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedUpdate:
    staging_dir: Path
    payload_dir: Path
    app_dir: Path
    version: str
    edition: str

    def cleanup(self):
        shutil.rmtree(self.staging_dir, ignore_errors=True)


def auto_update_supported():
    return sys.platform == 'win32' and bool(getattr(sys, 'frozen', False))


def detect_edition(app_dir=None):
    root = Path(app_dir) if app_dir else Path(sys.executable).resolve().parent
    if any((root / p).is_dir() for p in ('runtime/cuda', '_internal/runtime/cuda')):
        return 'full-cuda'
    if (root / '_internal/.models').is_dir():
        return 'full'
    return 'lite'


def _validate_download_url(url, redirected=False):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise UpdateInstallError('Update downloads require trusted HTTPS URLs')
    if redirected and parsed.hostname in ('release-assets.githubusercontent.com', 'objects.githubusercontent.com'):
        return
    if (parsed.hostname != 'github.com' or
            not parsed.path.startswith('/zxbb1190/VoxGo_game_voice_trans/releases/download/') or
            not parsed.path.lower().endswith('.zip')):
        raise UpdateInstallError('Update package must come from the official GitHub release')


class _TrustedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_download_url(newurl, redirected=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_package(url, checksum, destination, progress=None):
    _validate_download_url(url)
    if not re.fullmatch(r'[0-9a-fA-F]{64}', checksum or ''):
        raise UpdateInstallError('Update manifest is missing a valid SHA256 checksum')
    digest = hashlib.sha256()
    received = 0
    opener = urllib.request.build_opener(_TrustedRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'VoxGo-Updater'})
    try:
        with opener.open(request, timeout=30) as response, open(destination, 'wb') as output:
            _validate_download_url(response.geturl(), redirected=True)
            total = int(response.headers.get('Content-Length', 0))
            if total < 0 or total > MAX_DOWNLOAD_BYTES:
                raise UpdateInstallError('Update package exceeds download limit')
            if total and shutil.disk_usage(Path(destination).parent).free < total + 256 * 1024**2:
                raise UpdateInstallError('Not enough disk space for update download')
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > MAX_DOWNLOAD_BYTES:
                    raise UpdateInstallError('Update package exceeds download limit')
                output.write(chunk)
                digest.update(chunk)
                if progress:
                    progress(received, total)
        if digest.hexdigest() != checksum.lower():
            raise UpdateInstallError('Update checksum mismatch; installation cancelled')
    except Exception:
        Path(destination).unlink(missing_ok=True)
        raise


def _archive_parts(name):
    # Validate Windows semantics even when tests run on Linux.
    name = name.replace('\\', '/')
    parts = name.rstrip('/').split('/')
    reserved = re.compile(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', re.I)
    if (not name or name.startswith('/') or any(
        not p or p in ('.', '..') or p.endswith((' ', '.')) or
        any(ord(c) < 32 or c in ':<>"|?*' for c in p) or reserved.match(p)
        for p in parts
    )):
        raise UpdateInstallError('Unsafe path in update archive')
    return parts


def extract_package(archive, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(archive) as package:
            entries = package.infolist()
            if not entries or len(entries) > MAX_ARCHIVE_ENTRIES:
                raise UpdateInstallError('Invalid update archive entry count')
            size = sum(item.file_size for item in entries)
            if size > MAX_EXTRACTED_BYTES or shutil.disk_usage(destination).free < size + 256 * 1024**2:
                raise UpdateInstallError('Update archive too large or insufficient disk space')
            seen = set()
            validated = []
            for item in entries:
                parts = _archive_parts(item.filename)
                mode = item.external_attr >> 16
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR) or item.flag_bits & 1:
                    raise UpdateInstallError('Links, special files and encrypted entries are not allowed')
                key = '/'.join(parts).casefold()
                if key in seen:
                    raise UpdateInstallError('Duplicate archive paths')
                seen.add(key)
                validated.append((item, parts))
            for item, parts in validated:
                path = destination.joinpath(*parts)
                if item.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with package.open(item) as source, path.open('xb') as target:
                        shutil.copyfileobj(source, target, 1024 * 1024)
        roots = list(destination.iterdir())
        payload = destination
        if len(roots) == 1 and roots[0].is_dir():
            payload = roots[0]
        if not (payload / 'VoxGo.exe').is_file() or not (payload / '_internal').is_dir():
            raise UpdateInstallError('Archive is not a VoxGo portable application')
        return payload
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def prepare_update(update: UpdateInfo, progress=None, edition=None):
    if not auto_update_supported():
        raise UpdateInstallError('Automatic installation requires the packaged Windows application')
    edition = edition or detect_edition()
    if edition not in ('lite', 'full', 'full-cuda'):
        raise UpdateInstallError('Unknown update edition')
    suffix = edition.replace('-', '_')
    url = getattr(update, 'download_' + suffix + '_url')
    checksum = getattr(update, 'sha256_' + suffix)
    app_dir = Path(sys.executable).resolve().parent
    stage = Path(tempfile.mkdtemp(prefix='VoxGo-update-')).resolve()
    try:
        if stage == app_dir or app_dir in stage.parents:
            raise UpdateInstallError('Update staging directory must be outside the application')
        archive = stage / 'package.zip'
        download_package(url, checksum, archive, progress)
        payload = extract_package(archive, stage / 'extracted')
        archive.unlink()
        return PreparedUpdate(stage, payload, app_dir, update.latest, edition)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


# JSON input avoids interpolating paths or user-controlled strings into code.
_HELPER = r'''
param([string]$PlanPath)
$ErrorActionPreference = 'Stop'
$plan = Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
$stage = Split-Path -Parent $PlanPath
$log = Join-Path $stage 'install.log'
$candidate = $plan.app + '.update-' + [guid]::NewGuid().ToString('N')
$backup = $plan.app + '.backup-' + [guid]::NewGuid().ToString('N')
$movedOld = $false
$installed = $false
$exited = $false
function Copy-SafeTree($source, $target, $cacheRoot = '') {
    $entry = Get-Item -LiteralPath $source -Force
    if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        # Hugging Face snapshots use file symlinks to blobs. Directory links
        # are never followed, and resolved files must remain in this cache.
        if ($entry.PSIsContainer -or -not $cacheRoot) { throw 'Unsupported reparse point in application data' }
        $resolved = [VoxGoUpdatePaths]::ResolveFile($source)
        $boundary = [IO.Path]::GetFullPath($cacheRoot).TrimEnd('\') + '\'
        if (-not $resolved.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Model cache link escapes its cache directory'
        }
        Copy-Item -LiteralPath $resolved -Destination $target -Force
    } elseif ($entry.PSIsContainer) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        foreach ($child in Get-ChildItem -LiteralPath $source -Force) {
            Copy-SafeTree $child.FullName (Join-Path $target $child.Name) $cacheRoot
        }
    } else {
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
}
try {
    $process = Get-Process -Id $plan.pid -ErrorAction Stop
    # Accessing Handle pins this specific process, avoiding PID reuse races.
    $handle = $process.Handle
    if ($process.Path -ne (Join-Path $plan.app 'VoxGo.exe')) { throw 'Running executable mismatch' }
    Set-Content -LiteralPath (Join-Path $stage 'ready') -Value 'ready'
    if (-not $process.WaitForExit(120000)) { throw 'Application did not exit within two minutes; update cancelled' }
    $exited = $true
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class VoxGoUpdatePaths {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern uint GetFinalPathNameByHandle(SafeFileHandle h, StringBuilder b, uint n, uint flags);
    public static string ResolveFile(string path) {
        using (var f = File.OpenRead(path)) {
            var text = new StringBuilder(32768);
            uint n = GetFinalPathNameByHandle(f.SafeFileHandle, text, (uint)text.Capacity, 0);
            if (n == 0 || n >= text.Capacity) throw new IOException("Cannot resolve model cache link");
            string result = text.ToString();
            if (result.StartsWith(@"\\?\UNC\")) return @"\\" + result.Substring(8);
            return result.StartsWith(@"\\?\") ? result.Substring(4) : result;
        }
    }
}
'@
    foreach ($root in @($plan.app, $plan.payload)) {
        if ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point app root' }
    }
    Copy-SafeTree $plan.payload $candidate
    foreach ($relative in $plan.preserve) {
        $source = Join-Path $plan.app $relative
        $target = Join-Path $candidate $relative
        if (Test-Path -LiteralPath $source) {
            $ancestor = Split-Path -Parent $source
            while ($ancestor -and $ancestor -ne $plan.app) {
                if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point in preserved path' }
                $ancestor = Split-Path -Parent $ancestor
            }
            if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force -Recurse }
            New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
            $cacheRoot = ''
            if ($relative -in @('.models', '.translation-models', '.translation_models',
                                '_internal/.models', '_internal/.translation_models')) {
                # Resolve any parent junctions before comparing a file target.
                if ((Get-Item -LiteralPath $source -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                    throw 'Model cache root cannot be a reparse point'
                }
                $cacheRoot = $source
            }
            Copy-SafeTree $source $target $cacheRoot
        }
    }
    Move-Item -LiteralPath $plan.app -Destination $backup
    $movedOld = $true
    Move-Item -LiteralPath $candidate -Destination $plan.app
    $installed = $true
    $restarted = Start-Process -FilePath (Join-Path $plan.app 'VoxGo.exe') -WorkingDirectory $plan.app -PassThru
    if ($restarted.WaitForExit(3000) -and $restarted.ExitCode -ne 0) { throw 'Updated application failed during startup' }
    # Retain backup for recovery; it is never silently deleted.
    Set-Content -LiteralPath (Join-Path $stage 'success') -Value $backup
} catch {
    $_ | Out-String | Add-Content -LiteralPath $log
    if ($movedOld) {
        try {
            if ($installed) { Remove-Item -LiteralPath $plan.app -Recurse -Force }
            Move-Item -LiteralPath $backup -Destination $plan.app
            Start-Process -FilePath (Join-Path $plan.app 'VoxGo.exe') -WorkingDirectory $plan.app
        } catch { $_ | Out-String | Add-Content -LiteralPath $log }
    }
    elseif ($exited) {
        try { Start-Process -FilePath (Join-Path $plan.app 'VoxGo.exe') -WorkingDirectory $plan.app }
        catch { $_ | Out-String | Add-Content -LiteralPath $log }
    }
    Set-Content -LiteralPath (Join-Path $stage 'failed') -Value ('Update failed. See ' + $log)
    exit 1
} finally {
    if (Test-Path -LiteralPath $candidate) { Remove-Item -LiteralPath $candidate -Recurse -Force -ErrorAction SilentlyContinue }
}
'''


def launch_update(prepared: PreparedUpdate):
    """Launch detached installer; caller MUST exit only after this returns.

    Does not request elevation. Installation on a read-only location fails with
    the current application left intact and a diagnostic log in staging_dir.
    """
    if not auto_update_supported():
        raise UpdateInstallError('Automatic installation requires the packaged Windows application')
    if prepared.app_dir.resolve() != Path(sys.executable).resolve().parent:
        raise UpdateInstallError('Prepared update belongs to a different application')
    if not (prepared.payload_dir / 'VoxGo.exe').is_file():
        raise UpdateInstallError('Prepared update is no longer available')
    # Fail before exiting if a sibling cannot be created at this location.
    try:
        with tempfile.TemporaryDirectory(prefix='.voxgo-write-test-', dir=prepared.app_dir.parent):
            pass
    except OSError as exc:
        raise UpdateInstallError('Application directory is not writable') from exc
    # Candidate and old installation coexist during the transaction.
    required = sum(p.stat().st_size for p in prepared.payload_dir.rglob('*') if p.is_file())
    for relative in PRESERVE_PATHS:
        source = prepared.app_dir / relative
        if source.is_file():
            required += source.stat().st_size
        elif source.is_dir():
            required += sum(p.stat().st_size for p in source.rglob('*') if p.is_file())
    if shutil.disk_usage(prepared.app_dir.parent).free < required + 256 * 1024**2:
        raise UpdateInstallError('Not enough disk space to install update while retaining rollback backup')
    plan = prepared.staging_dir / 'plan.json'
    plan.write_text(json.dumps({'app': str(prepared.app_dir), 'payload': str(prepared.payload_dir),
                               'pid': os.getpid(), 'preserve': PRESERVE_PATHS}), encoding='utf-8')
    helper = prepared.staging_dir / 'install.ps1'
    helper.write_text(_HELPER, encoding='utf-8-sig')
    ready = prepared.staging_dir / 'ready'
    ready.unlink(missing_ok=True)
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    process = subprocess.Popen(
        [str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
         '-File', str(helper), '-PlanPath', str(plan)],
        cwd=str(prepared.staging_dir), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ready.exists():
            return process
        if process.poll() is not None:
            break
        time.sleep(0.05)
    process.terminate()
    process.wait(timeout=5)
    raise UpdateInstallError('Update helper failed to start; application remains open. See ' + str(prepared.staging_dir))
