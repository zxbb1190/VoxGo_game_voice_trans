param([ValidateSet('ja','ko','ru')][string]$Language='ja',[string]$Id='', [ValidateRange(1,10)][int]$Repeats=1)
$ErrorActionPreference='Stop'
$testRoot=Split-Path -Parent $PSScriptRoot
$manifest=Get-Content -LiteralPath (Join-Path $testRoot 'materials\manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$rows=@($manifest | Where-Object {$_.language -eq $Language})
if($Id){$rows=@($rows | Where-Object {$_.id -eq $Id})}
if(-not $rows.Count){throw 'No licensed audio matches the selection'}
$row=@($rows | Sort-Object -Property rms_dbfs -Descending)[0]
$audio=[IO.Path]::GetFullPath((Join-Path $testRoot $row.audio))
$materialRoot=[IO.Path]::GetFullPath((Join-Path $testRoot 'materials'))+[IO.Path]::DirectorySeparatorChar
if(-not $audio.StartsWith($materialRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Audio path escapes materials'}
$stream=[IO.File]::OpenRead($audio)
try{$hash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($stream))).Replace('-','').ToLowerInvariant()}finally{$stream.Dispose()}
if($hash -ne $row.sha256){throw 'Audio SHA-256 mismatch'}
$log=Join-Path $testRoot 'evidence\playback.jsonl'
$player=New-Object Media.SoundPlayer($audio)
try {
    $player.Load()
    for($repeat=1;$repeat -le $Repeats;$repeat++) {
        @{event='play_begin';utc=[DateTime]::UtcNow.ToString('o');id=$row.id;language=$Language;domain='public_encyclopedic_read_speech';repeat=$repeat} | ConvertTo-Json -Compress | Add-Content -LiteralPath $log -Encoding UTF8
        $player.PlaySync()
        @{event='play_end';utc=[DateTime]::UtcNow.ToString('o');id=$row.id;repeat=$repeat} | ConvertTo-Json -Compress | Add-Content -LiteralPath $log -Encoding UTF8
        if($repeat -lt $Repeats){Start-Sleep -Seconds 4}
    }
} finally {$player.Dispose()}
