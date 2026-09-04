param (
    [Parameter(Mandatory=$false)]
    [string]$ApkFolder = $PSScriptRoot,

    [Parameter(Mandatory=$false)]
    [string]$Repo = "nullcpy/apks"
)

# Ensure gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "[-] Error: GitHub CLI ('gh') is not installed or not in PATH." -ForegroundColor Red
    Write-Host "    Install it via: 'winget install GitHub.cli' or from https://cli.github.com" -ForegroundColor Yellow
    exit 1
}

# Ensure gh CLI is authenticated
$authCheck = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Error: GitHub CLI is not authenticated." -ForegroundColor Red
    Write-Host "    Please run 'gh auth login' to log into your GitHub account." -ForegroundColor Yellow
    exit 1
}

# Ensure the target folder exists
if (-not (Test-Path $ApkFolder)) {
    Write-Host "[-] Error: Folder '$ApkFolder' does not exist." -ForegroundColor Red
    exit 1
}

Push-Location $ApkFolder

try {
    # Find all .apk, .apkm, and .xapk files
    $apks = Get-ChildItem -Path . -Include *.apk, *.apkm, *.xapk -Recurse

    if ($apks -eq $null -or $apks.Count -eq 0) {
        Write-Host "[!] No .apk, .apkm, or .xapk files found in '$ApkFolder'." -ForegroundColor Yellow
        exit 0
    }

    Write-Host "[+] Found $($apks.Count) APK(s) to process for repository '$Repo'." -ForegroundColor Green

    foreach ($apk in $apks) {
        $fileName = $apk.Name
        
        # Ensure proper naming format: <package_name>-<version>[-<version_code>]-<arch>.<ext>
        if (-not $fileName.Contains('-') -or $fileName.StartsWith('-')) {
            Write-Host "[-] Skipping '$fileName': file name does not follow '<pkg_name>-<version>...<ext>' convention." -ForegroundColor Yellow
            continue
        }

        # Extract package name (everything before the first '-')
        $packageName = $fileName.Split('-')[0]

        if (-not $packageName.Contains('.')) {
            Write-Host "[-] Skipping '$fileName': '$packageName' does not look like a valid Android package name (e.g. com.example.app)." -ForegroundColor Yellow
            continue
        }
        
        Write-Host "================================================="
        Write-Host "[*] Processing: $fileName"
        Write-Host "[*] Package / Tag: $packageName"
        
        # Check if the release (tag) already exists on GitHub
        $null = gh release view $packageName --repo $Repo 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[+] Release '$packageName' exists. Uploading asset..." -ForegroundColor Cyan
            # --clobber allows overwriting if the same exact file name already exists in the release
            gh release upload $packageName $apk.FullName --repo $Repo --clobber
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[+] Successfully uploaded $fileName to '$packageName'." -ForegroundColor Green
                Remove-Item $apk.FullName -Force
                Write-Host "[*] Removed $fileName from local folder." -ForegroundColor Gray
            } else {
                Write-Host "[-] Failed to upload $fileName to '$packageName'." -ForegroundColor Red
            }
        } else {
            Write-Host "[+] Release '$packageName' does not exist. Creating and uploading..." -ForegroundColor Yellow
            
            # Create a new release and upload the file at the same time
            gh release create $packageName $apk.FullName --repo $Repo --title $packageName --notes ""
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[+] Successfully created release '$packageName' and uploaded $fileName." -ForegroundColor Green
                Remove-Item $apk.FullName -Force
                Write-Host "[*] Removed $fileName from local folder." -ForegroundColor Gray
            } else {
                Write-Host "[-] Failed to create release '$packageName'." -ForegroundColor Red
            }
        }
    }

    Write-Host "================================================="
    Write-Host "[+] All done!" -ForegroundColor Green

} finally {
    Pop-Location
}
