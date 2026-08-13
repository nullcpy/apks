import os
import json
import re
import subprocess
import sys
import time
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
# How many recent versions of an app to unconditionally protect from deletion.
KEEP_COUNT = 10

# How many days a version must be inactive before it is eligible for deletion.
KEEP_DAYS = 30
# ==========================================

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}\n{result.stderr}")
        return None
    return result.stdout.strip()

def parse_gh_time(time_str):
    # '2024-08-13T10:30:46Z' -> epoch timestamp
    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    return int(dt.timestamp())

def cleanup_releases():
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("GITHUB_REPOSITORY environment variable not set.")
        sys.exit(1)

    print(f"--- Fetching all releases for repo: {repo} ---")
    
    releases_file = "releases_new.json"
    if not os.path.exists(releases_file):
        print(f"File {releases_file} not found.")
        sys.exit(1)

    with open(releases_file, 'r', encoding='utf-8') as f:
        releases = json.load(f)

    usage_file = "usage.json"
    usage_data = {}
    if os.path.exists(usage_file):
        try:
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
        except Exception as e:
            print(f"Failed to load usage.json: {e}")

    suffix_pattern = re.compile(
        r'-(all|arm-v7a|arm64-v8a|common|universal|x86|x86_64|armeabi-v7a)\.(apk|apkm|xapk|apks)$',
        re.IGNORECASE
    )

    current_time = int(time.time())
    expire_sec = KEEP_DAYS * 24 * 60 * 60
    usage_data_changed = False
    all_existing_versions = set()

    for release in releases:
        tag = release.get("tag_name")
        assets = release.get("assets", [])
        if not assets:
            continue

        print(f"\n--- Processing release: {tag} ---")
        
        version_groups = {}
        for asset in assets:
            name = asset['name']
            version_key = suffix_pattern.sub('', name)
            all_existing_versions.add(version_key)
            
            if version_key not in version_groups:
                version_groups[version_key] = []
            version_groups[version_key].append(asset)

        # Determine last active timestamp for each version
        version_scores = {}
        for v_key, v_assets in version_groups.items():
            gh_time = max(parse_gh_time(a['created_at']) for a in v_assets)
            tracked_time = usage_data.get(v_key, 0)
            
            # Index manually uploaded or legacy files directly into usage.json
            if tracked_time == 0:
                usage_data[v_key] = gh_time
                usage_data_changed = True
                
            version_scores[v_key] = max(gh_time, tracked_time)

        sorted_versions = sorted(
            version_groups.items(),
            key=lambda x: version_scores[x[0]],
            reverse=True
        )

        to_keep_versions = sorted_versions[:KEEP_COUNT]
        remaining_versions = sorted_versions[KEEP_COUNT:]
        
        to_delete_versions = []
        for v_key, v_assets in remaining_versions:
            score = version_scores[v_key]
            if (current_time - score) > expire_sec:
                to_delete_versions.append((v_key, v_assets))
            else:
                to_keep_versions.append((v_key, v_assets))

        if not to_delete_versions:
            print(f"Found {len(sorted_versions)} versions, none meet deletion criteria.")
            continue

        print(f"Keeping {len(to_keep_versions)} versions.")
        for v_key, v_assets in to_keep_versions:
            last_active = datetime.utcfromtimestamp(version_scores[v_key]).strftime('%Y-%m-%d')
            print(f"  {v_key} ({len(v_assets)} assets) [Active: {last_active}]")

        print(f"Deleting {len(to_delete_versions)} versions (inactive > 30 days):")
        for v_key, v_assets in to_delete_versions:
            last_active = datetime.utcfromtimestamp(version_scores[v_key]).strftime('%Y-%m-%d')
            print(f"  {v_key} ({len(v_assets)} assets) [Active: {last_active}]")
            for asset in v_assets:
                asset_id = asset['id']
                asset_name = asset['name']
                print(f"    Deleting asset: {asset_name} (ID: {asset_id})")
                cmd = f'gh api -X DELETE repos/{repo}/releases/assets/{asset_id}'
                run_cmd(cmd)
            
            if v_key in usage_data:
                del usage_data[v_key]
                usage_data_changed = True

    ghost_keys = [k for k in usage_data.keys() if k not in all_existing_versions]
    if ghost_keys:
        print(f"\n--- Pruning {len(ghost_keys)} missing versions from usage.json ---")
        for gk in ghost_keys:
            print(f"  Removing ghost entry: {gk}")
            del usage_data[gk]
        usage_data_changed = True

    if usage_data_changed:
        print("\n--- Updating usage.json ---")
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, indent=2)
        run_cmd("git config user.name 'github-actions[bot]'")
        run_cmd("git config user.email 'github-actions[bot]@users.noreply.github.com'")
        run_cmd("git add usage.json")
        run_cmd("git commit -m 'chore: prune deleted versions from usage.json'")
        run_cmd("git push origin main")
        print("Successfully pruned usage.json.")

if __name__ == "__main__":
    cleanup_releases()
