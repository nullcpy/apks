#!/usr/bin/env bash
#
# upload_apks.sh - Bash equivalent of upload_apks.ps1 (Linux / macOS).
#
# Uploads .apk / .apkm / .xapk files into the GitHub Releases cache of the
# RVB stock-APK repo (one release per Android package name) and deletes the
# local file after a successful upload. Requires the GitHub CLI (`gh`).
#
# Works with the stock macOS bash 3.2 (no arrays, mapfile or globstar).

set -euo pipefail

# ==========================================
# CONFIGURATION (same defaults as upload_apks.ps1)
# ==========================================
REPO="nullcpy/apks"
APK_FOLDER=""
# ==========================================

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
RESET='\033[0m'

# Drop the colors when output is piped or written to a log
if [ ! -t 1 ]; then
    RED='' GREEN='' YELLOW='' CYAN='' GRAY='' RESET=''
fi

plain()   { printf '%b\n' "$*"; }
red()     { printf '%b\n' "${RED}$*${RESET}"; }
green()   { printf '%b\n' "${GREEN}$*${RESET}"; }
yellow()  { printf '%b\n' "${YELLOW}$*${RESET}"; }
cyan()    { printf '%b\n' "${CYAN}$*${RESET}"; }
gray()    { printf '%b\n' "${GRAY}$*${RESET}"; }

usage() {
    cat <<'EOF'
Usage: upload_apks.sh [options] [<apk-folder>]

Uploads every *.apk / *.apkm / *.xapk found under <apk-folder> (recursive)
into GitHub Releases of the cache repo, one release per Android package
name. The local file is deleted after a successful upload.

Options:
  -d, --apk-folder <path>   Folder to scan for APKs (default: folder of this script)
  -r, --repo <owner/name>   Target repository (default: nullcpy/apks)
  -h, --help                Show this help and exit

Requires: gh (GitHub CLI), authenticated via `gh auth login`.
EOF
}

# ------------------------------------------
# Argument parsing
# ------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        -d|--apk-folder|--apkfolder)
            [ $# -ge 2 ] || { red "[-] Error: $1 requires a value."; exit 1; }
            APK_FOLDER="$2"; shift 2 ;;
        --apk-folder=*|--apkfolder=*)
            APK_FOLDER="${1#*=}"; shift ;;
        -r|--repo)
            [ $# -ge 2 ] || { red "[-] Error: $1 requires a value."; exit 1; }
            REPO="$2"; shift 2 ;;
        --repo=*)
            REPO="${1#*=}"; shift ;;
        -h|--help)
            usage; exit 0 ;;
        -*)
            red "[-] Error: unknown option '$1'."
            usage
            exit 1 ;;
        *)
            APK_FOLDER="$1"; shift ;;
    esac
done

# Default: the folder this script lives in (mirrors $PSScriptRoot)
[ -n "$APK_FOLDER" ] || APK_FOLDER="$SCRIPT_DIR"

# ------------------------------------------
# Preconditions
# ------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
    red "[-] Error: GitHub CLI ('gh') is not installed or not in PATH."
    yellow "    Install it via 'brew install gh' (macOS), 'apt install gh' (Linux)"
    yellow "    or from https://cli.github.com"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    red "[-] Error: GitHub CLI is not authenticated."
    yellow "    Please run 'gh auth login' to log into your GitHub account."
    exit 1
fi

if [ ! -d "$APK_FOLDER" ]; then
    red "[-] Error: Folder '$APK_FOLDER' does not exist."
    exit 1
fi

# Resolve to an absolute path; on Git Bash prefer the native Windows form so
# that gh.exe receives a path it can open ('pwd -W' is unknown on Linux/macOS).
resolved="$(CDPATH= cd -- "$APK_FOLDER" && pwd -W 2>/dev/null || true)"
[ -n "$resolved" ] || resolved="$(CDPATH= cd -- "$APK_FOLDER" && pwd)"
APK_FOLDER="$resolved"

# ------------------------------------------
# Collect APKs (recursive, case-insensitive)
# ------------------------------------------
FOUND_LIST="$(mktemp)"
trap 'rm -f "$FOUND_LIST"' EXIT

find "$APK_FOLDER" -type f \
    \( -iname '*.apk' -o -iname '*.apkm' -o -iname '*.xapk' \) -print \
    | LC_ALL=C sort -f > "$FOUND_LIST"

count="$(grep -c . "$FOUND_LIST" || true)"
if [ "$count" -eq 0 ]; then
    yellow "[!] No .apk, .apkm, or .xapk files found in '$APK_FOLDER'."
    exit 0
fi

green "[+] Found $count APK(s) to process for repository '$REPO'."

# ------------------------------------------
# Process each file
# ------------------------------------------
failed=0

while IFS= read -r file; do
    [ -n "$file" ] || continue
    name="${file##*/}"

    # Ensure proper naming format: <pkg_name>-<version>[-<version_code>]-<arch>.<ext>
    # -> the name must contain a '-' and must not start with one (patterns are
    #    matched in order, so the leading '-' case has to come first)
    case "$name" in
        -*)
            yellow "[-] Skipping '$name': file name does not follow '<pkg_name>-<version>...<ext>' convention."
            continue ;;
        *-*)
            ;;
        *)
            yellow "[-] Skipping '$name': file name does not follow '<pkg_name>-<version>...<ext>' convention."
            continue ;;
    esac

    # Extract package name (everything before the first '-')
    package_name="${name%%-*}"

    case "$package_name" in
        *.*) ;;
        *)
            yellow "[-] Skipping '$name': '$package_name' does not look like a valid Android package name (e.g. com.example.app)."
            continue ;;
    esac

    plain "================================================="
    plain "[*] Processing: $name"
    plain "[*] Package / Tag: $package_name"

    # Check if the release (tag) already exists on GitHub
    if gh release view "$package_name" --repo "$REPO" >/dev/null 2>&1; then
        cyan "[+] Release '$package_name' exists. Uploading asset..."
        # --clobber allows overwriting if the same exact file name already exists
        if gh release upload "$package_name" "$file" --repo "$REPO" --clobber; then
            green "[+] Successfully uploaded $name to '$package_name'."
            rm -f "$file"
            gray "[*] Removed $name from local folder."
        else
            red "[-] Failed to upload $name to '$package_name'."
            failed=$((failed + 1))
        fi
    else
        yellow "[+] Release '$package_name' does not exist. Creating and uploading..."
        # Create a new release and upload the file at the same time
        if gh release create "$package_name" "$file" --repo "$REPO" --title "$package_name" --notes " "; then
            green "[+] Successfully created release '$package_name' and uploaded $name."
            rm -f "$file"
            gray "[*] Removed $name from local folder."
        else
            red "[-] Failed to create release '$package_name'."
            failed=$((failed + 1))
        fi
    fi
done < "$FOUND_LIST"

plain "================================================="
if [ "$failed" -eq 0 ]; then
    green "[+] All done!"
    exit 0
fi
yellow "[!] Finished with $failed failure(s) - see the messages above."
exit 1
