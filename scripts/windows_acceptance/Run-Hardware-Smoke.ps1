param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$settingsPath=Join-Path $root 'candidate\user_settings.json'
$manifest=Get-Content -LiteralPath (Join-Path $root 'materials\manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$results=@()
foreach($language in @('ja','ko','ru')) {
    $settings=Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $settings.translation.source_lang=$language;$settings.translation.target_lang='zh'
    $settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
    $started=[DateTime]::UtcNow
    $wrapper=Start-Process -FilePath powershell.exe -ArgumentList @('-NoProfile','-File',('"'+(Join-Path $PSScriptRoot 'Start-Acceptance.ps1')+'"')) -WindowStyle Hidden -PassThru
    $session=$null
    try {
        for($attempt=0;$attempt -lt 80;$attempt++) {
            if($wrapper.HasExited){throw 'Acceptance wrapper failed before candidate startup'}
            $path=Join-Path $root 'evidence\session.json'
            if(Test-Path -LiteralPath $path) {
                $saved=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
                if([DateTimeOffset]::Parse($saved.started_utc).UtcDateTime -ge $started -and $saved.source_lang -eq $language){$session=$saved;break}
            }
            Start-Sleep -Milliseconds 250
        }
        if(-not $session){throw 'No fresh candidate session'}
        Start-Sleep -Seconds 9
        $row=@($manifest | Where-Object {$_.language -eq $language} | Sort-Object -Property rms_dbfs -Descending)[0]
        & (Join-Path $PSScriptRoot 'Play-Audio.ps1') -Language $language -Id $row.id -Repeats 1
        Start-Sleep -Seconds 7
        $running=Get-Process -Id $session.candidate_pid -ErrorAction Stop
        $results+=@{language=$language;audio_id=$row.id;candidate_pid=$running.Id;responding=$running.Responding;window_title=$running.MainWindowTitle;ended_utc=[DateTime]::UtcNow.ToString('o');shutdown='supervisor_terminate_after_smoke_not_crash';real_translation_api_requests=0}
    } finally {
        if($session) {
            $running=Get-Process -Id $session.candidate_pid -ErrorAction SilentlyContinue
            if($running -and $running.Path -eq (Join-Path $root 'candidate\VoxGo.exe')) {Stop-Process -Id $running.Id}
        }
        $wrapper.WaitForExit(5000)|Out-Null
    }
    $results | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $root 'evidence\hardware-smoke.json') -Encoding UTF8
}
# Restore only the test locale; keep every other test setting and all evidence.
$settings=Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$settings.translation.source_lang='ja';$settings.translation.target_lang='zh'
$settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
