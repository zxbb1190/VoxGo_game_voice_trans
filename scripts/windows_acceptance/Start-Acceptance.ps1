param([int]$Port = 17853)
$ErrorActionPreference = 'Stop'
$testRoot = Split-Path -Parent $PSScriptRoot
$candidate = Join-Path $testRoot 'candidate'
$exe = Join-Path $candidate 'VoxGo.exe'
if(@(Get-Process -Name VoxGo -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe}).Count){throw 'This acceptance candidate is already running; close it normally before starting another session.'}
$settingsPath = Join-Path $candidate 'user_settings.json'
$authorityPath = Join-Path $candidate 'telemetry_consent.json'
$settings = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$authority = Get-Content -LiteralPath $authorityPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($authority.telemetry_consent -ne 'denied' -or $authority.telemetry_epoch -ne '' -or $settings.app.telemetry_consent -ne 'denied') {
    throw 'Full telemetry must remain denied. Do not reset/delete identity; restore the test-only denied consent before launch.'
}
if ($settings.translation.api_key) { throw 'API Key must be empty in this no-online-call package, including Google; no real or fixture keys are accepted.' }
if ($settings.translation.provider -eq 'openai_compatible') {
    $endpoint=[uri]$settings.translation.endpoint
    if ($endpoint.Host -ne '127.0.0.1' -or $endpoint.Port -ne $Port -or $endpoint.Scheme -ne 'http') { throw 'Only the local acceptance endpoint is allowed.' }
} elseif ($settings.translation.provider -ne 'google' -and $settings.translation.provider -ne 'local') { throw 'Unsupported acceptance provider.' }
$expectedExe='cf49af8bd00e257ce11ae3904fa8ec6a7a4d307089e91df35df82020e302aa93'
$stream=[IO.File]::OpenRead($exe)
try { $actualExe=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($stream))).Replace('-','').ToLowerInvariant() } finally {$stream.Dispose()}
if ($actualExe -ne $expectedExe) { throw 'Candidate EXE differs from the caed9130 Full build.' }
$evidence=Join-Path $testRoot 'evidence'
New-Item -ItemType Directory -Path $evidence -Force | Out-Null
$stopFile=Join-Path $evidence ('stop-'+[guid]::NewGuid().ToString('N'))
$helper=Join-Path $PSScriptRoot 'LocalOnlyServer.ps1'
$server=$null;$client=$null
try {
    $server=Start-Process -FilePath powershell.exe -ArgumentList @('-NoProfile','-File',('"'+$helper+'"'),'-Port',$Port,'-Evidence',('"'+$evidence+'"'),'-StopFile',('"'+$stopFile+'"')) -WindowStyle Hidden -PassThru
    $healthy=$false
    for($attempt=0;$attempt -lt 60;$attempt++) {
        try { $web=New-Object Net.WebClient;$web.Proxy=$null;$health=$web.DownloadString("http://127.0.0.1:$Port/_acceptance/health") | ConvertFrom-Json;$web.Dispose(); if($health.scope -eq 'VoxGo-caed9130-local-only'){$healthy=$true;break} } catch {}
        if($server.HasExited){throw 'Local-only server exited before startup'}
        Start-Sleep -Milliseconds 250
    }
    if(-not $healthy){throw 'Local-only network gate unavailable; candidate was not started'}
    $info=New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName=$exe;$info.WorkingDirectory=$candidate;$info.UseShellExecute=$false
    $info.Arguments='--config "'+(Join-Path $candidate 'acceptance.config.json')+'"'
    $info.EnvironmentVariables['HTTP_PROXY']="http://127.0.0.1:$Port"
    $info.EnvironmentVariables['HTTPS_PROXY']="http://127.0.0.1:$Port"
    $info.EnvironmentVariables['ALL_PROXY']="http://127.0.0.1:$Port"
    $info.EnvironmentVariables['NO_PROXY']='127.0.0.1,localhost,::1'
    $info.EnvironmentVariables['QT_QPA_PLATFORM']='windows'
    $client=[System.Diagnostics.Process]::Start($info)
    $session=@{candidate_pid=$client.Id;wrapper_pid=$PID;server_pid=$server.Id;started_utc=[DateTime]::UtcNow.ToString('o');source_lang=$settings.translation.source_lang;root=$testRoot;proxy="http://127.0.0.1:$Port";full='denied';real_api_key_copied=$false}
    $session | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'session.json') -Encoding UTF8
    $session | ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $evidence 'session-history.jsonl') -Encoding UTF8
    $lastCpu=0.0;$clock=[Diagnostics.Stopwatch]::StartNew();$lastWall=0.0
    $csv=Join-Path $evidence 'process-samples.csv'
    while(-not $client.WaitForExit(1000)) {
        $client.Refresh();$cpu=$client.TotalProcessorTime.TotalSeconds;$wall=$clock.Elapsed.TotalSeconds
        $pct=100*($cpu-$lastCpu)/[Math]::Max(0.001,$wall-$lastWall)
        [pscustomobject]@{utc=[DateTime]::UtcNow.ToString('o');process_id=$client.Id;cpu_one_core_percent=[Math]::Round($pct,2);rss_bytes=$client.WorkingSet64;peak_rss_bytes=$client.PeakWorkingSet64} | Export-Csv -LiteralPath $csv -Append -NoTypeInformation -Encoding UTF8
        $lastCpu=$cpu;$lastWall=$wall
    }
    @{exit_code=$client.ExitCode;ended_utc=[DateTime]::UtcNow.ToString('o');external_forwarded=0;real_translation_api_requests=0} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'session-ended.json') -Encoding UTF8
} finally {
    # The rejection endpoint stays alive until after the candidate exits.
    if($client -and -not $client.HasExited){$client.WaitForExit()}
    New-Item -ItemType File -Path $stopFile -Force | Out-Null
    if($server -and -not $server.HasExited){$server.WaitForExit(3000)|Out-Null}
}
