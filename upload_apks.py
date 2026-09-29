#!/usr/bin/env python3
"""
upload_apks.py - Python equivalent of upload_apks.ps1 / upload_apks.sh.

Uploads .apk / .apkm / .xapk files into the GitHub Releases cache of the RVB
stock-APK repo (one release per Android package name) and deletes the local
file after a successful upload. Requires the GitHub CLI (`gh`).

Runs on any OS with Python 3.8+ (standard library only).
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ==========================================
# CONFIGURATION (same defaults as upload_apks.ps1)
# ==========================================
REPO = "nullcpy/apks"
APK_EXTENSIONS = (".apk", ".apkm", ".xapk")
# ==========================================

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
GRAY = "\033[0;90m"
RESET = "\033[0m"

# Drop the colors when output is piped or written to a log.
if not sys.stdout.isatty():
    RED = GREEN = YELLOW = CYAN = GRAY = RESET = ""


def plain(msg: str) -> None:
    print(msg, flush=True)


def red(msg: str) -> None:
    print(f"{RED}{msg}{RESET}", flush=True)


def green(msg: str) -> None:
    print(f"{GREEN}{msg}{RESET}", flush=True)


def yellow(msg: str) -> None:
    print(f"{YELLOW}{msg}{RESET}", flush=True)


def cyan(msg: str) -> None:
    print(f"{CYAN}{msg}{RESET}", flush=True)


def gray(msg: str) -> None:
    print(f"{GRAY}{msg}{RESET}", flush=True)


def gh(*args: str, capture: bool = False) -> int:
    """Run a gh subcommand and return its exit code."""
    result = subprocess.run(
        ["gh", *args],
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
    )
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="upload_apks.py",
        description=(
            "Upload every *.apk / *.apkm / *.xapk found under <apk-folder> "
            "(recursive) into GitHub Releases of the cache repo, one release "
            "per Android package name. The local file is deleted after a "
            "successful upload."
        ),
        epilog="Requires: gh (GitHub CLI), authenticated via `gh auth login`.",
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="folder to scan for APKs (default: folder of this script)",
    )
    parser.add_argument(
        "-d", "--apk-folder", "--apkfolder",
        dest="apk_folder",
        default=None,
        help="folder to scan for APKs (overrides the positional argument)",
    )
    parser.add_argument(
        "-r", "--repo",
        default=REPO,
        help=f"target repository as owner/name (default: {REPO})",
    )
    return parser.parse_args()


def find_apks(folder: Path) -> list:
    """Recursive, case-insensitive match on .apk / .apkm / .xapk."""
    apks = [p for p in folder.rglob("*")
            if p.is_file() and p.suffix.lower() in APK_EXTENSIONS]
    return sorted(apks, key=lambda p: str(p).lower())


def extract_package_name(file_name: str):
    """Return the package name (before the first '-'), or None if malformed."""
    if "-" not in file_name or file_name.startswith("-"):
        return None
    return file_name.split("-")[0]


def upload(path: Path, package_name: str, repo: str) -> bool:
    """Upload one APK, creating the release first when it does not exist."""
    file_name = path.name

    # Check if the release (tag) already exists on GitHub
    if gh("release", "view", package_name, "--repo", repo, capture=True) == 0:
        cyan(f"[+] Release '{package_name}' exists. Uploading asset...")
        # --clobber allows overwriting if the same file name already exists
        if gh("release", "upload", package_name, str(path),
              "--repo", repo, "--clobber") == 0:
            green(
                f"[+] Successfully uploaded {file_name} to '{package_name}'.")
            return True
        red(f"[-] Failed to upload {file_name} to '{package_name}'.")
        return False

    yellow(
        f"[+] Release '{package_name}' does not exist. Creating and uploading...")
    # Create a new release and upload the file at the same time
    if gh("release", "create", package_name, str(path),
          "--repo", repo, "--title", package_name, "--notes", " ") == 0:
        green(
            f"[+] Successfully created release '{package_name}' and uploaded {file_name}.")
        return True
    red(f"[-] Failed to create release '{package_name}'.")
    return False


def resolve_folder(args: argparse.Namespace):
    """Return the folder to scan, mirroring the $PSScriptRoot default."""
    if args.apk_folder:
        folder = Path(os.path.expanduser(args.apk_folder))
    elif args.folder:
        folder = Path(os.path.expanduser(args.folder))
    else:
        folder = Path(__file__).resolve().parent
    if not folder.is_dir():
        red(f"[-] Error: Folder '{folder}' does not exist.")
        return None
    return folder.resolve()


def main() -> int:
    args = parse_args()

    # Ensure gh CLI is installed
    if shutil.which("gh") is None:
        red("[-] Error: GitHub CLI ('gh') is not installed or not in PATH.")
        yellow("    Install it via 'brew install gh' (macOS), 'apt install gh' (Linux)")
        yellow("    or from https://cli.github.com")
        return 1

    # Ensure gh CLI is authenticated
    if gh("auth", "status", capture=True) != 0:
        red("[-] Error: GitHub CLI is not authenticated.")
        yellow("    Please run 'gh auth login' to log into your GitHub account.")
        return 1

    folder = resolve_folder(args)
    if folder is None:
        return 1

    apks = find_apks(folder)
    if not apks:
        yellow(f"[!] No .apk, .apkm, or .xapk files found in '{folder}'.")
        return 0

    green(
        f"[+] Found {len(apks)} APK(s) to process for repository '{args.repo}'.")

    failed = 0
    for apk in apks:
        # Ensure proper naming format: <pkg_name>-<version>[-<version_code>]-<arch>.<ext>
        package_name = extract_package_name(apk.name)
        if package_name is None:
            yellow(f"[-] Skipping '{apk.name}': file name does not follow "
                   "'<pkg_name>-<version>...<ext>' convention.")
            continue

        if "." not in package_name:
            yellow(f"[-] Skipping '{apk.name}': '{package_name}' does not look like a "
                   "valid Android package name (e.g. com.example.app).")
            continue

        plain("=================================================")
        plain(f"[*] Processing: {apk.name}")
        plain(f"[*] Package / Tag: {package_name}")

        if upload(apk, package_name, args.repo):
            apk.unlink()
            gray(f"[*] Removed {apk.name} from local folder.")
        else:
            failed += 1

    plain("=================================================")
    if failed == 0:
        green("[+] All done!")
        return 0
    yellow(f"[!] Finished with {failed} failure(s) - see the messages above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
