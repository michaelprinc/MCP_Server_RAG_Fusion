param(
    [Parameter(Mandatory = $true)]
    [string]$SqlclExecutable,

    [Parameter(Mandatory = $false)]
    [ValidateRange(30, 3600)]
    [int]$TimeoutSeconds = 120,

    [Parameter(Mandatory = $false)]
    [string]$ServerName = "sqlcl",

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = "$env:APPDATA\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SqlclExecutable)) {
    throw "SQLcl executable not found: $SqlclExecutable"
}

$configDir = Split-Path -Path $ConfigPath -Parent
if (-not (Test-Path -LiteralPath $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

if (Test-Path -LiteralPath $ConfigPath) {
    $raw = Get-Content -LiteralPath $ConfigPath -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) {
        $config = [pscustomobject]@{}
    }
    else {
        $config = $raw | ConvertFrom-Json
    }

    $backupPath = "$ConfigPath.bak.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item -LiteralPath $ConfigPath -Destination $backupPath -Force
}
else {
    $config = [pscustomobject]@{}
}

if ($null -eq $config.PSObject.Properties["mcpServers"]) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([pscustomobject]@{})
}

$serverConfig = [pscustomobject]@{
    type = "stdio"
    command = $SqlclExecutable
    args = @("-mcp")
    disabled = $false
    timeout = $TimeoutSeconds
}

$config.mcpServers | Add-Member -MemberType NoteProperty -Name $ServerName -Value $serverConfig -Force

$json = $config | ConvertTo-Json -Depth 20
Set-Content -LiteralPath $ConfigPath -Value $json -Encoding UTF8

Write-Host "Cline MCP configuration updated:"
Write-Host "  ConfigPath: $ConfigPath"
Write-Host "  ServerName: $ServerName"
Write-Host "  SQLcl path: $SqlclExecutable"
Write-Host "  Timeout:    $TimeoutSeconds s"
