$ErrorActionPreference = 'Stop'

function Read-AllowedSiliconFlowCredential([string]$SettingsPath) {
    if (-not (Test-Path -LiteralPath $SettingsPath -PathType Leaf)) {
        throw 'Existing SiliconFlow settings are unavailable; no provider/model substitution is allowed.'
    }
    try { $data = Get-Content -LiteralPath $SettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { throw 'Existing SiliconFlow settings cannot be read; no request was made.' }
    $translation = $data.translation
    $allowedEndpoints = @('https://api.siliconflow.cn/v1', 'https://api.siliconflow.cn/v1/', 'https://api.siliconflow.cn/v1/chat/completions', 'https://api.siliconflow.cn/v1/chat/completions/')
    if ($translation.provider -cne 'openai_compatible' -or $translation.model -cne 'tencent/Hunyuan-MT-7B' -or
        $translation.endpoint -cnotin $allowedEndpoints -or [string]::IsNullOrWhiteSpace($translation.api_key) -or
        $translation.api_key -match '^(YOUR_|REPLACE_|<)' -or $translation.api_key -match '[\r\n]') {
        throw 'Existing SiliconFlow/Hunyuan-MT-7B configuration is unavailable; no request was made.'
    }
    return $translation
}

function Test-OnlineAcceptanceProfile([string]$Candidate, [int]$Port) {
    $baseline = Get-Content -LiteralPath (Join-Path $Candidate 'acceptance.config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($name in @('acceptance.config.json', 'user_settings.json')) {
        $value = Get-Content -LiteralPath (Join-Path $Candidate $name) -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($value.app.telemetry_consent -cne 'denied' -or $value.app.telemetry_epoch -ne '' -or
            $value.app.telemetry_consent_version -ne 3 -or -not $value.app.setup_completed) {
            throw 'Full telemetry must remain denied with empty epoch and completed test setup.'
        }
        $translation = $value.translation
        $localBase = 'http://127.0.0.1:' + $Port + '/v1'
        if ($translation.provider -cne 'openai_compatible' -or $translation.model -cne 'tencent/Hunyuan-MT-7B' -or
            $translation.endpoint -cnotin @($localBase, ($localBase + '/chat/completions')) -or
            ($translation.api_key -and $translation.api_key -cnotmatch '^local-acceptance-[a-f0-9]{32}$')) {
            throw 'Candidate must use the local relay and fixed Hunyuan model; never place a real key in this profile.'
        }
        # The shipped settings writer persists a whitelist, not the whole config.
        # Missing settings inherit the explicit --config baseline; explicit unsafe
        # overrides still fail. This also allows normal GUI save/restart cycles.
        $localOnly = $baseline.whisper.local_files_only
        if ($value.whisper -and $value.whisper.PSObject.Properties['local_files_only']) { $localOnly = $value.whisper.local_files_only }
        $mobileHost = $baseline.websocket.host
        if ($value.websocket -and $value.websocket.PSObject.Properties['host']) { $mobileHost = $value.websocket.host }
        $updates = $baseline.update.enabled
        if ($value.update -and $value.update.PSObject.Properties['enabled']) { $updates = $value.update.enabled }
        if ($updates -or -not $localOnly -or $mobileHost -cne '127.0.0.1') {
            throw 'Test profile must disable updates/downloads and bind the mobile server to loopback.'
        }
    }
    $consent = Get-Content -LiteralPath (Join-Path $Candidate 'telemetry_consent.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($consent.telemetry_consent -cne 'denied' -or $consent.telemetry_epoch -ne '' -or $consent.telemetry_consent_version -ne 3) {
        throw 'Durable Full consent must remain denied; do not reset or delete identities.'
    }
}

function Set-LocalAcceptanceToken([string]$Candidate, [string]$Token) {
    $path = Join-Path $Candidate 'user_settings.json'
    $settings = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    $settings.translation.api_key = $Token
    $temporary = Join-Path $Candidate ('relay-settings-' + [guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($temporary, ($settings | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
        # Windows PowerShell coerces $null to an empty string for a string
        # parameter. File.Replace requires a genuine CLR null for no backup.
        [IO.File]::Replace($temporary, $path, [NullString]::Value)
    } finally {
        # Replacement failures must not leave a local session token behind in
        # a temporary settings file. The original target remains untouched.
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}
