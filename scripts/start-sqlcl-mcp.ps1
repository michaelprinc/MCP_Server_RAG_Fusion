param(
    [Parameter(Mandatory = $false)]
    [string]$SqlclExecutable,

    [Parameter(Mandatory = $false)]
    [ValidateSet("auto", "sql", "java")]
    [string]$LaunchMode = "auto",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Stderr {
    param([string]$Message)
    [Console]::Error.WriteLine($Message)
}

function Test-ExistingFile {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $false
    }
    return (Test-Path -LiteralPath $PathValue -PathType Leaf)
}

function Resolve-ExecutableFromPath {
    $candidate = Get-Command "sql.exe" -ErrorAction SilentlyContinue
    if ($null -ne $candidate) {
        return $candidate.Source
    }

    $candidate = Get-Command "sql" -ErrorAction SilentlyContinue
    if ($null -ne $candidate) {
        return $candidate.Source
    }

    return $null
}

function Convert-ToVersion {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return [version]"0.0.0.0"
    }

    $normalized = $Text -replace "[^0-9\.]", ""
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        return [version]"0.0.0.0"
    }

    try {
        return [version]$normalized
    }
    catch {
        return [version]"0.0.0.0"
    }
}

function Get-BestExtensionSqlcl {
    $roots = @(
        (Join-Path $env:USERPROFILE ".vscode\extensions"),
        (Join-Path $env:USERPROFILE ".vscode-insiders\extensions")
    )

    $candidates = @()

    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) {
            continue
        }

        $dirs = Get-ChildItem -Path $root -Directory -Filter "oracle.sql-developer-*" -ErrorAction SilentlyContinue
        foreach ($dir in $dirs) {
            $sqlPath = Join-Path $dir.FullName "dbtools\sqlcl\bin\sql.exe"
            if (-not (Test-Path -LiteralPath $sqlPath -PathType Leaf)) {
                continue
            }

            $versionText = $dir.Name -replace "^oracle\.sql-developer-", ""
            $candidates += [pscustomobject]@{
                Version = Convert-ToVersion -Text $versionText
                SqlPath = $sqlPath
            }
        }
    }

    if ($candidates.Count -eq 0) {
        return $null
    }

    return ($candidates | Sort-Object Version -Descending | Select-Object -First 1).SqlPath
}

function Resolve-SqlclExecutable {
    param([string]$UserPath)

    if (Test-ExistingFile -PathValue $UserPath) {
        return (Resolve-Path -LiteralPath $UserPath).Path
    }

    if (Test-ExistingFile -PathValue $env:SQLCL_MCP_SQL_PATH) {
        return (Resolve-Path -LiteralPath $env:SQLCL_MCP_SQL_PATH).Path
    }

    $pathResolved = Resolve-ExecutableFromPath
    if (-not [string]::IsNullOrWhiteSpace($pathResolved)) {
        return $pathResolved
    }

    $extensionResolved = Get-BestExtensionSqlcl
    if (-not [string]::IsNullOrWhiteSpace($extensionResolved)) {
        return $extensionResolved
    }

    throw "SQLcl executable was not found. Set -SqlclExecutable or SQLCL_MCP_SQL_PATH."
}

function Get-ExtensionLayout {
    param([string]$ResolvedSqlPath)

    $binDir = Split-Path -Path $ResolvedSqlPath -Parent
    $sqlclDir = Split-Path -Path $binDir -Parent
    $dbtoolsDir = Split-Path -Path $sqlclDir -Parent

    if ([string]::IsNullOrWhiteSpace($dbtoolsDir)) {
        return $null
    }

    $javaExe = Join-Path $dbtoolsDir "jdk\bin\java.exe"
    $launchDir = Join-Path $dbtoolsDir "sqlcl\launch"

    if ((Test-Path -LiteralPath $javaExe -PathType Leaf) -and (Test-Path -LiteralPath $launchDir -PathType Container)) {
        return [pscustomobject]@{
            JavaExe = $javaExe
            LaunchDir = $launchDir
        }
    }

    return $null
}

$resolvedSql = Resolve-SqlclExecutable -UserPath $SqlclExecutable
$extensionLayout = Get-ExtensionLayout -ResolvedSqlPath $resolvedSql

$resolvedMode = $LaunchMode
if ($resolvedMode -eq "auto") {
    if ($null -ne $extensionLayout) {
        $resolvedMode = "java"
    }
    else {
        $resolvedMode = "sql"
    }
}

if ($resolvedMode -eq "java" -and $null -eq $extensionLayout) {
    throw "LaunchMode 'java' requires SQL Developer extension layout with embedded JDK."
}

if ($resolvedMode -eq "sql") {
    $command = $resolvedSql
    $arguments = @("-mcp")
}
else {
    $command = $extensionLayout.JavaExe
    $arguments = @(
        "--add-modules", "ALL-DEFAULT",
        "--add-opens", "java.prefs/java.util.prefs=oracle.dbtools.win32",
        "--add-opens", "jdk.security.auth/com.sun.security.auth.module=oracle.dbtools.win32",
        "-Djava.net.useSystemProxies=true",
        "-p", $extensionLayout.LaunchDir,
        "-m", "oracle.dbtools.sqlcl.app",
        "-mcp"
    )
}

if ($DryRun) {
    Write-Stderr ("SQLCL_MCP dry run")
    Write-Stderr ("  SqlclExecutable: " + $resolvedSql)
    Write-Stderr ("  LaunchMode:      " + $resolvedMode)
    Write-Stderr ("  Command:         " + $command)
    Write-Stderr ("  Arguments:       " + ($arguments -join " "))
    exit 0
}

& $command @arguments
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) {
    $exitCode = 0
}

if ($exitCode -ne 0) {
    Write-Stderr ("SQLcl MCP process exited with code " + $exitCode)
}

exit $exitCode
