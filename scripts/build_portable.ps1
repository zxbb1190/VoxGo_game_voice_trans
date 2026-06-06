param(
    [string]$Version = "0.2.2",
    [switch]$SkipLite,
    [switch]$SkipFull
)

$ErrorActionPreference = "Stop"

$Python = ".\.venv-win\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Missing $Python. Create .venv-win and install requirements first."
}
if (-not (Test-Path ".\.venv-win\Scripts\pyinstaller.exe")) {
    & $Python -m pip install pyinstaller==6.11.1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller."
    }
}

New-Item -ItemType Directory -Force release | Out-Null

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments
    )

    $argumentLine = ($Arguments | ForEach-Object {
        if ($_ -match '[\s";]') {
            '"' + ($_.Replace('"', '\"')) + '"'
        } else {
            $_
        }
    }) -join " "

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $argumentLine `
        -NoNewWindow `
        -Wait `
        -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Command failed with exit code $($process.ExitCode): $FilePath $($Arguments -join ' ')"
    }
}

function Build-Portable {
    param(
        [string]$Edition,
        [string]$IncludeModel
    )

    if ($IncludeModel -eq "1") {
        $modelRoot = ".models\models--Systran--faster-whisper-small"
        $modelRef = Join-Path $modelRoot "refs\main"
        $hasModelCache = $false
        if (Test-Path $modelRef) {
            $snapshot = (Get-Content $modelRef -Raw).Trim()
            if ($snapshot) {
                $snapshotRoot = Join-Path $modelRoot ("snapshots\" + $snapshot)
                $hasModelCache = (
                    (Test-Path (Join-Path $snapshotRoot "config.json")) -and
                    (Test-Path (Join-Path $snapshotRoot "model.bin")) -and
                    (Test-Path (Join-Path $snapshotRoot "tokenizer.json")) -and
                    (Test-Path (Join-Path $snapshotRoot "vocabulary.txt"))
                )
            }
        }
        if (-not $hasModelCache) {
            Invoke-Checked $Python @(
                "-c",
                "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='.models')"
            )
        } else {
            Write-Host "Using existing faster-whisper-small cache."
        }
    }

    $env:INCLUDE_MODEL = $IncludeModel
    $env:INCLUDE_CUDA_RUNTIME = "0"

    Remove-Item -Recurse -Force "dist\VoxGo" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "build\VoxGo" -ErrorAction SilentlyContinue
    Invoke-Checked $Python @("-m", "PyInstaller", "--clean", "--noconfirm", "VoxGo.spec")

    $packageName = "VoxGo-v$Version-$Edition"
    $packageDir = "release\$packageName"
    $zipPath = "release\$packageName.zip"

    Remove-Item -Recurse -Force $packageDir -ErrorAction SilentlyContinue
    Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
    Copy-Item -Recurse "dist\VoxGo" $packageDir
    Compress-Archive -Path $packageDir -DestinationPath $zipPath -CompressionLevel Optimal

    $hash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $size = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
    Write-Host "$packageName.zip"
    Write-Host "  size: $size MB"
    Write-Host "  sha256: $hash"
}

if (-not $SkipLite) {
    Build-Portable -Edition "lite" -IncludeModel "0"
}

if (-not $SkipFull) {
    Build-Portable -Edition "full" -IncludeModel "1"
}

Remove-Item Env:\INCLUDE_MODEL -ErrorAction SilentlyContinue
Remove-Item Env:\INCLUDE_CUDA_RUNTIME -ErrorAction SilentlyContinue
