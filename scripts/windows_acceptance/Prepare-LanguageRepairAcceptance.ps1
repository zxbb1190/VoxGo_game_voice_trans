param(
    [Parameter(Mandatory=$true)][string]$FullDirectory,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedExeSha256,
    [Parameter(Mandatory=$true)][string]$TemplateAcceptanceRoot,
    [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference='Stop'
$full=(Resolve-Path -LiteralPath $FullDirectory).Path
$template=(Resolve-Path -LiteralPath $TemplateAcceptanceRoot).Path
$target=[IO.Path]::GetFullPath($Destination)
if(Test-Path -LiteralPath $target){throw 'Destination exists; use a fresh directory. Existing packages are never overwritten.'}
$actual=(Get-FileHash -LiteralPath (Join-Path $full 'VoxGo.exe') -Algorithm SHA256).Hash.ToLowerInvariant()
if($actual -cne $ExpectedExeSha256.ToLowerInvariant()){throw 'Full EXE does not match the explicitly pinned build hash.'}
$package=Get-Content -LiteralPath (Join-Path $full '_internal\package-info.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($package.package_type -cne 'full'){throw 'A built Full CPU package is required.'}
$baseline=Get-Content -LiteralPath (Join-Path $template 'candidate\acceptance.config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($baseline.translation.api_key -or $baseline.app.telemetry_consent -cne 'denied'){throw 'Only an empty-key, Full-denied acceptance template is allowed.'}
foreach($name in @('candidate','control','evidence','materials')){New-Item -ItemType Directory -Path (Join-Path $target $name) -Force | Out-Null}
$candidate=Join-Path $target 'candidate'
Get-ChildItem -LiteralPath $full -Force | Copy-Item -Destination $candidate -Recurse
Get-ChildItem -LiteralPath (Join-Path $template 'materials') -Force | Copy-Item -Destination (Join-Path $target 'materials') -Recurse
Get-ChildItem -LiteralPath $PSScriptRoot -File | Copy-Item -Destination (Join-Path $target 'control')
# Only the new physical copy receives its new build pin. Old launchers and
# artifacts retain their original immutable caed9130 checks.
foreach($name in @('Start-Acceptance.ps1','Start-OnlineAcceptance.ps1')){
    $path=Join-Path $target ('control\'+$name)
    $text=[IO.File]::ReadAllText($path)
    $pin='cf49af8bd00e257ce11ae3904fa8ec6a7a4d307089e91df35df82020e302aa93'
    if(-not $text.Contains($pin)){throw 'Unexpected launcher template; no hash guard was changed.'}
    $text=$text.Replace($pin,$actual).Replace("candidate='caed9130'","candidate='language-repair-20261026'").Replace('the caed9130 Full build','the pinned language repair Full build')
    [IO.File]::WriteAllText($path,$text,[Text.UTF8Encoding]::new($false))
}
$baseline.translation.source_lang='ja';$baseline.translation.target_lang='zh'
$baseline.translation.endpoint='http://127.0.0.1:17854/v1'
$baseline.translation.api_key=''
$baseline.whisper | Add-Member -NotePropertyName model_dir -NotePropertyValue (Join-Path $candidate '_internal\.models') -Force
$baseline.whisper | Add-Member -NotePropertyName multilingual_asr_strategy -NotePropertyValue 'language_aware' -Force
foreach($name in @('acceptance.config.json','user_settings.json')){
    [IO.File]::WriteAllText((Join-Path $candidate $name),($baseline | ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
}
[IO.File]::WriteAllText((Join-Path $candidate 'telemetry_consent.json'),'{"telemetry_consent":"denied","telemetry_consent_version":3,"telemetry_epoch":"","full_telemetry_source":"user_denied"}',[Text.UTF8Encoding]::new($false))
$commands=@{
    'Start-LOCAL-ONLY.cmd'='control\Start-Acceptance.ps1" -Port 17854';
    'Start-ONLINE-REAL-API.cmd'='control\Start-OnlineAcceptance.ps1" -RunOnline';
    'Preflight-ONLY-NO-API.cmd'='control\Start-OnlineAcceptance.ps1"';
    'Play-JA.cmd'='control\Play-Audio.ps1" -Language ja';
    'Play-KO.cmd'='control\Play-Audio.ps1" -Language ko';
    'Play-RU.cmd'='control\Play-Audio.ps1" -Language ru';
    'Collect-Diagnostics.cmd'='control\Collect-Diagnostics.ps1"'
}
foreach($entry in $commands.GetEnumerator()){
    $command="@echo off`r`ncd /d `"%~dp0`"`r`npowershell.exe -NoProfile -File `"%~dp0"+$entry.Value+"`r`npause`r`n"
    [IO.File]::WriteAllText((Join-Path $target $entry.Key),$command,[Text.Encoding]::ASCII)
}
[ordered]@{candidate='language-repair-20261026';exe_sha256=$actual;full='denied';api_key_copied=$false;real_api_requests_during_preparation=0;physical_copy=$true;release_approved=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $target 'preparation.json') -Encoding UTF8
Write-Output ('Prepared independent candidate: '+$target)
