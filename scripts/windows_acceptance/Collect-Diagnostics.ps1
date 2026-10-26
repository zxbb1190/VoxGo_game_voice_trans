param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$manifest=Get-Content -LiteralPath (Join-Path $root 'materials\manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$playFile=Join-Path $root 'evidence\playback.jsonl'
$plays=if(Test-Path $playFile){@(Get-Content -LiteralPath $playFile -Encoding UTF8 | ForEach-Object {$_ | ConvertFrom-Json})}else{@()}
$logPath=Join-Path $root 'candidate\app.log'
$lines=if(Test-Path $logPath){@(Get-Content -LiteralPath $logPath -Encoding UTF8)}else{@()}
$events=@()
foreach($line in $lines) {
    if($line -notmatch '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \|.*?\| (.*)$'){continue}
    $utc=[DateTimeOffset]::ParseExact(($matches[1]+' +08:00'),'yyyy-MM-dd HH:mm:ss zzz',[Globalization.CultureInfo]::InvariantCulture).UtcDateTime
    $message=$matches[2]
    if($message -match '\[recognition\]|sent to whisper:|filtered transcription:|empty asr:|translation skipped:|\[延迟\]|translated:|\[翻译错误|\[未翻译\]'){
        $events+=@{utc=$utc;message=$message}
    }
}
$records=@();$review=@()
foreach($row in $manifest) {
    $begin=@($plays | Where-Object {$_.event -eq 'play_begin' -and $_.id -eq $row.id} | Select-Object -Last 1)
    $recognized=@();$drops=@();$latencies=@();$mock=$false
    if($begin.Count) {
        $start=[DateTimeOffset]::Parse($begin[0].utc).UtcDateTime
        $end=$start.AddSeconds([double]$row.seconds+8)
        foreach($event in $events | Where-Object {$_.utc -ge $start.AddSeconds(-1) -and $_.utc -le $end}) {
            $text=$event.message
            if($text -match '\[recognition\] (.*?) \(lang='){$recognized+=$matches[1]}
            elseif($text -match '^filtered transcription:|^empty asr:|^translation skipped:'){$drops+=($text -replace ', text=.*$','')}
            elseif($text -match '\[延迟\].*total=(\d+)ms'){$latencies+=[int]$matches[1]}
            if($text.Contains('【本地模拟，非真实翻译】')){$mock=$true}
        }
    }
    $records+=@{id=$row.id;language=$row.language;source=$row.source;domain='public_encyclopedic_read_speech';standard_transcript=$row.reference_text;recognized_fragments=$recognized;pipeline_drops=$drops;capture_enqueue_to_widget_ms=$latencies;translation= $(if($mock){'【本地模拟，非真实翻译】字幕链路已收到识别文本。'}else{''});human_review='pending';real_translation_api_requests=0}
    $review+=[pscustomobject]@{'音频ID'=$row.id;'语言'=$row.language;'来源与场景'='FLEURS/公开人类百科朗读，非游戏';'播放文件'=$row.audio;'标准转写'=$row.reference_text;'Whisper识别片段'=($recognized -join ' / ');'中文译文'= $(if($mock){'本地模拟字幕，非真实翻译；真实译文待授权'}else{'待实测/未产生模拟字幕'});'延迟说明'='分段入队→部件更新，不是语音结束→屏幕';'日志延迟ms'=($latencies -join ' / ');'Pipeline问题'=($drops -join ' / ');'问题等级'='待人工判定';'人工结论'='pending'}
}
$records | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $root 'evidence\public-audio-diagnostics.json') -Encoding UTF8
$review | Export-Csv -LiteralPath (Join-Path $root 'materials\manual-review-with-smoke.csv') -NoTypeInformation -Encoding UTF8
Write-Output 'Collected local public-audio windows only; no upload, no secret headers, no quality acceptance.'
