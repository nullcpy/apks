# nullcpy/apks

Central stock APK cache repository for [**RVB (ReVanced Builder)**](https://github.com/nullcpy/rvb).

This repository stores upstream stock APKs across tagged GitHub Releases (one release per package name). RVB checks this cache before attempting web scraping, ensuring ultra-fast, rate-limit-free builds on CI runners and local environments.

---

## 🤝 Become a Contributor

Uploading APKs requires write (collaborator) access to this repository.

If you want to contribute APKs to help maintain the cache:
👉 **Contact here to get added as a contributor:** [**https://t.me/rvb27/306**](https://t.me/rvb27/306)

Once added, follow the quick instructions below to submit APKs painlessly!

---

## 🚀 Quick Start: Submitting APKs

### 1. Prerequisites

You only need the **GitHub CLI (`gh`)** installed and authenticated:

- **Install `gh` (Windows):**
  ```powershell
  winget install GitHub.cli
  ```
  *(or via Scoop: `scoop install gh`)*

- **Authenticate:**
  ```powershell
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

1. **Clone the repository** (or pull the latest):
   ```powershell
   git clone https://github.com/nullcpy/apks.git
   cd apks
   ```

2. **Drop your renamed APK file(s)** directly into the `apks` folder.

3. **Run the upload script:**
   ```powershell
   .\upload_apks.ps1
   ```

**That's it!** The script automatically:
1. Inspects the APK filename and extracts the package name (e.g. `com.facebook.katana`).
2. Checks GitHub for an existing release tagged with that package name.
3. Uploads the APK to the release (or creates the release if it's the first time).
4. Cleans up the local APK file once uploaded so your directory stays tidy.

---

## 🛠️ Advanced Usage

If you prefer keeping your APKs in a separate download folder rather than moving them into the repo, specify `-ApkFolder`:

```powershell
.\upload_apks.ps1 -ApkFolder "C:\Users\YourName\Downloads"
```

---

## 🧹 Maintenance & Retention

A weekly GitHub Actions workflow (running every Sunday at midnight) (`cleanup-apks.py`) monitors `usage.json` and evicts older APK variants that have not been requested by RVB within 30 days, keeping the cache lean and within GitHub storage quotas.
