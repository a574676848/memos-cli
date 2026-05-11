param(
    [string] $PackageSpec = $env:MEMOS_CLI_PACKAGE_SPEC,
    [string] $PackageName = $env:MEMOS_CLI_PACKAGE_NAME,
    [string] $CommandName = $env:MEMOS_CLI_COMMAND_NAME,
    [string] $InstallManager = $env:MEMOS_CLI_INSTALL_MANAGER,
    [string] $Python = $env:PYTHON,
    [string] $VenvDir = $env:MEMOS_CLI_VENV_DIR,
    [string] $BinDir = $env:MEMOS_CLI_BIN_DIR
)

$scriptPath = Join-Path $PSScriptRoot "install.ps1"
$arguments = @{}
if (-not [string]::IsNullOrWhiteSpace($PackageSpec)) { $arguments.PackageSpec = $PackageSpec }
if (-not [string]::IsNullOrWhiteSpace($PackageName)) { $arguments.PackageName = $PackageName }
if (-not [string]::IsNullOrWhiteSpace($CommandName)) { $arguments.CommandName = $CommandName }
if (-not [string]::IsNullOrWhiteSpace($InstallManager)) { $arguments.InstallManager = $InstallManager }
if (-not [string]::IsNullOrWhiteSpace($Python)) { $arguments.Python = $Python }
if (-not [string]::IsNullOrWhiteSpace($VenvDir)) { $arguments.VenvDir = $VenvDir }
if (-not [string]::IsNullOrWhiteSpace($BinDir)) { $arguments.BinDir = $BinDir }

& $scriptPath @arguments
