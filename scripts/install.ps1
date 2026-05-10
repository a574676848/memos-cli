param(
    [string] $PackageSpec = $env:MEMOS_CLI_PACKAGE_SPEC,
    [string] $PackageName = $env:MEMOS_CLI_PACKAGE_NAME,
    [string] $CommandName = $env:MEMOS_CLI_COMMAND_NAME,
    [ValidateSet("auto", "pipx", "pip")]
    [string] $InstallManager = $env:MEMOS_CLI_INSTALL_MANAGER,
    [string] $Python = $env:PYTHON
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PackageSpec)) { $PackageSpec = "memos-cli" }
if ([string]::IsNullOrWhiteSpace($PackageName)) { $PackageName = "memos-cli" }
if ([string]::IsNullOrWhiteSpace($CommandName)) { $CommandName = "memos" }
if ([string]::IsNullOrWhiteSpace($InstallManager)) { $InstallManager = "auto" }
if ([string]::IsNullOrWhiteSpace($Python)) { $Python = "python" }

function Test-Command($Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PipxPackageInstalled {
    if (-not (Test-Command "pipx")) {
        return $false
    }
    $packages = (& pipx list --short 2>$null) | ForEach-Object { ($_ -split "\s+")[0] }
    return $packages -contains $PackageName
}

function Install-WithPipx {
    if (-not (Test-Command "pipx")) {
        throw "pipx is required but was not found."
    }

    if (Test-Command $CommandName) {
        if ((Test-PipxPackageInstalled) -and ($PackageSpec -eq $PackageName)) {
            Write-Host "memos-cli already exists, upgrading with pipx..."
            pipx upgrade $PackageName
        } else {
            Write-Host "memos-cli already exists, reinstalling package spec with pipx..."
            pipx install --force $PackageSpec
        }
    } else {
        Write-Host "Installing memos-cli with pipx..."
        pipx install $PackageSpec
    }
}

function Install-WithPipUser {
    Write-Host "Installing or upgrading memos-cli with pip --user..."
    & $Python -m pip install --user --upgrade $PackageSpec
}

if ($InstallManager -eq "pipx") {
    Install-WithPipx
} elseif ($InstallManager -eq "pip") {
    Install-WithPipUser
} else {
    if ((Test-Command "pipx") -and ((-not (Test-Command $CommandName)) -or (Test-PipxPackageInstalled))) {
        Install-WithPipx
    } else {
        Install-WithPipUser
    }
}

if (Test-Command $CommandName) {
    & $CommandName --version
} else {
    Write-Host "Installed package, but '$CommandName' is not on PATH yet."
    Write-Host "Add your Python user scripts directory to PATH, then run: $CommandName --version"
}
