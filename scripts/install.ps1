param(
    [string] $PackageSpec = $env:MEMOS_CLI_PACKAGE_SPEC,
    [string] $PackageName = $env:MEMOS_CLI_PACKAGE_NAME,
    [string] $CommandName = $env:MEMOS_CLI_COMMAND_NAME,
    [string] $InstallManager = $env:MEMOS_CLI_INSTALL_MANAGER,
    [string] $Python = $env:PYTHON,
    [string] $VenvDir = $env:MEMOS_CLI_VENV_DIR,
    [string] $BinDir = $env:MEMOS_CLI_BIN_DIR
)

$ErrorActionPreference = "Stop"
$script:InstalledCommandPath = $null

$DefaultPackageSpec = "git+https://github.com/a574676848/memos-cli.git"
if ([string]::IsNullOrWhiteSpace($PackageSpec)) { $PackageSpec = $DefaultPackageSpec }
if ([string]::IsNullOrWhiteSpace($PackageName)) { $PackageName = "memos-cli" }
if ([string]::IsNullOrWhiteSpace($CommandName)) { $CommandName = "memos" }
if ([string]::IsNullOrWhiteSpace($InstallManager)) { $InstallManager = "auto" }
if ([string]::IsNullOrWhiteSpace($Python)) { $Python = "python" }
if ([string]::IsNullOrWhiteSpace($VenvDir)) { $VenvDir = Join-Path $env:LOCALAPPDATA "memos-cli\venv" }
if ([string]::IsNullOrWhiteSpace($BinDir)) { $BinDir = Join-Path $HOME ".local\bin" }
if (@("auto", "pipx", "pip", "venv") -notcontains $InstallManager) {
    throw "InstallManager must be one of: auto, pipx, pip, venv."
}

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
    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($null -ne $command) { $script:InstalledCommandPath = $command.Source }
}

function Install-WithPipUser {
    Write-Host "Installing or upgrading memos-cli with pip --user..."
    & $Python -m pip install --user --upgrade $PackageSpec
    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($null -ne $command) { $script:InstalledCommandPath = $command.Source }
}

function Install-WithVenv {
    Write-Host "Installing or upgrading memos-cli in isolated venv..."
    & $Python -m venv $VenvDir
    & (Join-Path $VenvDir "Scripts\python.exe") -m pip install --upgrade pip
    & (Join-Path $VenvDir "Scripts\python.exe") -m pip install --upgrade $PackageSpec

    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    $target = Join-Path $VenvDir "Scripts\$CommandName.exe"
    $cmdPath = Join-Path $BinDir "$CommandName.cmd"
    $content = "@echo off`r`n`"$target`" %*`r`n"
    $encoding = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($cmdPath, $content, $encoding)
    $script:InstalledCommandPath = $cmdPath
}

if ($InstallManager -eq "pipx") {
    Install-WithPipx
} elseif ($InstallManager -eq "pip") {
    Install-WithPipUser
} elseif ($InstallManager -eq "venv") {
    Install-WithVenv
} else {
    if ((Test-Command "pipx") -and ((-not (Test-Command $CommandName)) -or (Test-PipxPackageInstalled))) {
        Install-WithPipx
    } else {
        Install-WithVenv
    }
}

if (-not [string]::IsNullOrWhiteSpace($script:InstalledCommandPath) -and (Test-Path $script:InstalledCommandPath)) {
    & $script:InstalledCommandPath --version
} elseif (Test-Command $CommandName) {
    & $CommandName --version
} else {
    Write-Host "Installed package, but '$CommandName' is not on PATH yet."
    Write-Host "Add '$BinDir' to PATH, then run: $CommandName --version"
}
