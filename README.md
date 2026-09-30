# nullcpy/apks

Central stock APK cache repository for [**RVB (ReVanced Builder)**](https://github.com/nullcpy/rvb).

This repository stores upstream stock APKs across tagged GitHub Releases (one release per package name). RVB checks this cache before attempting web scraping, ensuring ultra-fast, rate-limit-free builds on CI runners and local environments.

---

## 🤝 Become a Contributor

Uploading APKs requires write (collaborator) access to this repository.

If you want to contribute APKs to help maintain the cache:
👉 **Contact here to get added as a contributor:** [**https://t.me/rvb27/306**](https://t.me/rvb27/306)

Once added, follow the quick instructions below to submit APKs painlessly!

> [!NOTE]
> Uploading works on **Windows, Linux and macOS** - the repository ships three
> equivalent scripts (`upload_apks.ps1`, `upload_apks.sh`, `upload_apks.py`).
> Use whichever fits your system.

---

## 🚀 Quick Start: Submitting APKs

### 1. Prerequisites

You only need the **GitHub CLI (`gh`)** installed and authenticated:

| OS | Install `gh` |
| :--- | :--- |
| **Windows** | `winget install GitHub.cli` *(or via Scoop: `scoop install gh`)* |
| **macOS** | `brew install gh` |
| **Linux (Debian/Ubuntu)** | `sudo apt install gh` |
| **Linux (other distros)** | See https://github.com/cli/cli#installation |

- **Authenticate** (identical on every OS):
  ```bash
  gh auth login
  ```
  *(Select `GitHub.com` -> `HTTPS` -> Log in with a web browser)*

---

### 2. File Naming Convention (Important!)

RVB organizes releases by **Android package name**, and identifies APKs by their filename. 

Your APK file **must** follow this format:

```text
<package_name>-<version>-<arch>.<ext>
```
or with a target version code:
```text
<package_name>-<version>-<version_code>-<arch>.<ext>
```

#### Examples:

| App | Correct Filename |
| :--- | :--- |
| **YouTube** | `com.google.android.youtube-20.08.37-arm64-v8a.apk` |
| **Twitter / X** | `com.twitter.android-10.80.0-all.apk` |
| **Facebook (arm64)** | `com.facebook.katana-573.0.0.37.74-473623755-arm64-v8a.apk` |
| **Facebook (arm-v7a)**| `com.facebook.katana-573.0.0.37.74-473623748-arm-v7a.apk` |
| **Reddit** | `com.reddit.frontpage-2025.08.0-arm64-v8a.apk` |

> [!TIP]
> If you downloaded the APK from APKMirror (e.g. `com.facebook.katana_573.0.0.37.74-473623755_minAPI30(arm64-v8a)(nodpi)_apkmirror.com.apk`), simply rename it according to the table above before running the script.

---

### 3. Uploading (Painless & Automated)

Pick the script that matches your system - all three behave identically:

| Script | Runs on | Requires |
| :--- | :--- | :--- |
| `upload_apks.ps1` | Windows | PowerShell 5+ |
| `upload_apks.sh` | Linux, macOS, Git Bash | Bash (also works on the stock macOS bash 3.2) |
| `upload_apks.py` | Any OS | Python 3.8+ (no extra packages) |

1. **Get the repository** - either clone it or download a ZIP:

   **Option A - Git clone** (recommended, refresh later with `git pull`):
   ```bash
   git clone https://github.com/nullcpy/apks.git
   cd apks
   ```

   **Option B - ZIP download** (no Git needed): download
   [main.zip](https://github.com/nullcpy/apks/archive/refs/heads/main.zip)
   (or **Code -> Download ZIP** on the repo page), extract it, then enter the
   folder it creates - GitHub names it `apks-main`:
   ```bash
   cd apks-main
   ```
   A ZIP is a one-off snapshot, so re-download it whenever you want the latest
   scripts; uploading works either way because the scripts talk to GitHub
   through `gh` rather than through your local copy of the repo.

2. **Drop your renamed APK file(s)** directly into that repository folder (the
   one containing the upload scripts).

3. **Run the upload script:**

   **Windows (PowerShell):**
   ```powershell
   .\upload_apks.ps1
   ```

   **Linux / macOS (Bash):**
   ```bash
   bash upload_apks.sh
   ```

   **Any system (Python):**
   ```bash
   python3 upload_apks.py    # Windows: python upload_apks.py
   ```

**That's it!** The script automatically:
1. Inspects the APK filename and extracts the package name (e.g. `com.facebook.katana`).
2. Checks GitHub for an existing release tagged with that package name.
3. Uploads the APK to the release (or creates the release if it's the first time).
4. Cleans up the local APK file once uploaded so your directory stays tidy.

---

## 🛠️ Advanced Usage

If you prefer keeping your APKs in a separate download folder rather than moving them into the repo, point the script at that folder:

```powershell
.\upload_apks.ps1 -ApkFolder "C:\Users\YourName\Downloads"
```

```bash
bash upload_apks.sh --apk-folder ~/Downloads
python3 upload_apks.py --apk-folder ~/Downloads
```

The `sh` and `py` scripts also accept the folder as a plain argument:

```bash
bash upload_apks.sh ~/Downloads
python3 upload_apks.py ~/Downloads
```

To upload to a different repository (e.g. your own fork for testing), pass `-Repo` (PowerShell) or `--repo` / `-r` (bash, Python):

```bash
bash upload_apks.sh --repo myuser/apks
```

Run `bash upload_apks.sh --help` or `python3 upload_apks.py --help` for the full option list.

> [!WARNING]
> The scripts delete each APK from the scanned folder right after a successful
> upload. Point them at a folder you are fine with being emptied.

---

## 🧹 Maintenance & Retention

A weekly GitHub Actions workflow (running every Sunday at midnight) (`cleanup-apks.py`) monitors `usage.json` and evicts older APK variants that have not been requested by RVB within 30 days, keeping the cache lean and within GitHub storage quotas.

`usage.json` is machine-managed - both workflows that write it keep its keys sorted so
their commits stay readable. Do not add or reorder entries by hand: an upload you made
through the script is indexed automatically at its upload time, and an entry whose asset
no longer exists is pruned on the next run.

> [!NOTE]
> The full cache contract - how RVB reads and writes this repository, the retention
> rules, the `usage.json` key format and file ordering, plus a debugging checklist - is
> documented in the builder repo:
> [**nullcpy/rvb → docs/cache-repo.md**](https://github.com/nullcpy/rvb/blob/main/docs/cache-repo.md).
