param(
    [int]$Port = 17854,
    [Parameter(Mandatory=$true)][string]$Evidence,
    [Parameter(Mandatory=$true)][string]$StopFile,
    [Parameter(Mandatory=$true)][string]$CredentialSettings
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'OnlineAcceptance.Common.ps1')
$credential = Read-AllowedSiliconFlowCredential $CredentialSettings
$token = [Environment]::GetEnvironmentVariable('VOXGO_ONLINE_SESSION_TOKEN')
$instance = [Environment]::GetEnvironmentVariable('VOXGO_ONLINE_INSTANCE')
if ($token -cnotmatch '^local-acceptance-[a-f0-9]{32}$' -or $instance -cnotmatch '^[a-f0-9]{32}$') {
    throw 'Online relay must be started through the isolated launcher.'
}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -Path (Join-Path $PSScriptRoot 'SiliconFlowRelay.cs') -ReferencedAssemblies 'System.Web.Extensions'
$upstream = [VoxGoAcceptance.SiliconFlowUpstream]::new($credential.api_key)
$credential = $null
$relay = [VoxGoAcceptance.OnlineRelay]::new($Port, $token, $instance, $Evidence, $upstream)
$relay.Run($StopFile)
