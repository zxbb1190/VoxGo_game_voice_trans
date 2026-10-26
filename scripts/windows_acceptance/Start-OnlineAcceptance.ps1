param(
    [string]$CredentialSettings = 'E:\my\my\game_voice_translator\user_settings.json',
    [int]$Port = 17854,
    [switch]$RunOnline
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'OnlineAcceptance.Common.ps1')
$testRoot = Split-Path -Parent $PSScriptRoot
$candidate = Join-Path $testRoot 'candidate'
$exe = Join-Path $candidate 'VoxGo.exe'
Test-OnlineAcceptanceProfile $candidate $Port
$credential = Read-AllowedSiliconFlowCredential $CredentialSettings
$credential = $null
$stream = [IO.File]::OpenRead($exe)
try { $exeHash = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
finally { $stream.Dispose() }
if ($exeHash -cne 'cf49af8bd00e257ce11ae3904fa8ec6a7a4d307089e91df35df82020e302aa93') {
    throw 'Candidate EXE differs from the caed9130 Full build.'
}
if (-not $RunOnline) {
    [ordered]@{ mode='preflight_only'; candidate='caed9130'; exe_sha256=$exeHash; model='tencent/Hunyuan-MT-7B'; credential_present=$true; credential_copied=$false; full='denied'; real_api_requests=0; request_limit=$null; budget_limit=$null } | ConvertTo-Json
    return
}
if (@(Get-Process -Name VoxGo -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe }).Count) {
    throw 'This candidate is already running; close it normally first.'
}
$evidence = Join-Path $testRoot 'evidence'
New-Item -ItemType Directory -Path $evidence -Force | Out-Null
$instance = [guid]::NewGuid().ToString('N')
$token = 'local-acceptance-' + [guid]::NewGuid().ToString('N')
$stopFile = Join-Path $evidence ('stop-' + $instance)
$server = $null; $client = $null
$sourceBefore = (Get-FileHash -LiteralPath $CredentialSettings -Algorithm SHA256).Hash
try {
    $serverInfo = [Diagnostics.ProcessStartInfo]::new()
    $serverInfo.FileName = 'powershell.exe'; $serverInfo.UseShellExecute = $false
    $serverInfo.CreateNoWindow = $true; $serverInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $serverInfo.Arguments = '-NoProfile -File "' + (Join-Path $PSScriptRoot 'OnlineRelay.ps1') + '" -Port ' + $Port + ' -Evidence "' + $evidence + '" -StopFile "' + $stopFile + '" -CredentialSettings "' + $CredentialSettings + '"'
    $serverInfo.EnvironmentVariables['VOXGO_ONLINE_SESSION_TOKEN'] = $token
    $serverInfo.EnvironmentVariables['VOXGO_ONLINE_INSTANCE'] = $instance
    $server = [Diagnostics.Process]::Start($serverInfo)
    $healthy = $false
    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        try {
            $web = [Net.WebClient]::new(); $web.Proxy = $null
            try { $health = $web.DownloadString('http://127.0.0.1:' + $Port + '/_acceptance/health') | ConvertFrom-Json }
            finally { $web.Dispose() }
            if ($health.scope -ceq 'VoxGo-caed9130-online-hunyuan-only' -and $health.instance -ceq $instance -and -not $health.journal_failed) { $healthy = $true; break }
        } catch { }
        if ($server.HasExited) { throw 'Online relay failed to start; candidate was not launched.' }
        Start-Sleep -Milliseconds 250
    }
    if (-not $healthy) { throw 'Expected online relay unavailable; candidate was not launched.' }
    Set-LocalAcceptanceToken $candidate $token
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $exe; $info.WorkingDirectory = $candidate; $info.UseShellExecute = $false
    $info.Arguments = '--config "' + (Join-Path $candidate 'acceptance.config.json') + '"'
    foreach ($name in @('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY')) { $info.EnvironmentVariables[$name] = 'http://127.0.0.1:' + $Port }
    $info.EnvironmentVariables['NO_PROXY'] = '127.0.0.1,localhost,::1'
    $info.EnvironmentVariables['QT_QPA_PLATFORM'] = 'windows'
    $client = [Diagnostics.Process]::Start($info)
    $session = [ordered]@{ instance=$instance; started_utc=[DateTime]::UtcNow.ToString('o'); candidate_pid=$client.Id; wrapper_pid=$PID; server_pid=$server.Id; candidate='caed9130'; full='denied'; model='tencent/Hunyuan-MT-7B'; credential_copied=$false; request_limit=$null; budget_limit=$null; automatic_retries=$false; endpoint='http://127.0.0.1:17854/v1' }
    $session | ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $evidence 'online-sessions.jsonl') -Encoding UTF8
    $lastCpu = 0.0; $lastWall = 0.0; $clock = [Diagnostics.Stopwatch]::StartNew()
    while (-not $client.WaitForExit(1000)) {
        if ($server.HasExited) {
            # Only this exact child is stopped if its network fence disappears.
            $client.Kill(); $client.WaitForExit()
            throw 'Relay exited unexpectedly; this test candidate was stopped.'
        }
        $client.Refresh(); $cpu = $client.TotalProcessorTime.TotalSeconds; $wall = $clock.Elapsed.TotalSeconds
        [pscustomobject]@{ utc=[DateTime]::UtcNow.ToString('o'); process_id=$client.Id; cpu_one_core_percent=[Math]::Round(100 * ($cpu - $lastCpu) / [Math]::Max(.001, $wall - $lastWall), 2); rss_bytes=$client.WorkingSet64; peak_rss_bytes=$client.PeakWorkingSet64 } | Export-Csv -LiteralPath (Join-Path $evidence 'process-samples.csv') -Append -NoTypeInformation -Encoding UTF8
        $lastCpu = $cpu; $lastWall = $wall
    }
} finally {
    # Keep the rejecting proxy alive until after the candidate has exited.
    try {
        if ($client -and -not $client.HasExited) { $client.WaitForExit() }
        try { Set-LocalAcceptanceToken $candidate '' }
        catch { Write-Warning 'Could not clear the local-only session token; no real key was stored in the candidate.' }
    } finally {
        # A settings write failure must never leave the credential-holder alive.
        try { New-Item -ItemType File -Path $stopFile -Force | Out-Null }
        finally {
            if ($server -and -not $server.HasExited) {
                if (-not $server.WaitForExit(15000)) { $server.Kill(); $server.WaitForExit() }
            }
        }
    }
    $sourceAfter = (Get-FileHash -LiteralPath $CredentialSettings -Algorithm SHA256).Hash
    [ordered]@{ instance=$instance; ended_utc=[DateTime]::UtcNow.ToString('o'); existing_settings_unchanged=($sourceBefore -ceq $sourceAfter); credential_copied=$false; full='denied_required'; actual_api_attempts='see online-relay.jsonl; reserved before HTTP, includes failures'; release=$false } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'online-session-ended.json') -Encoding UTF8
}
