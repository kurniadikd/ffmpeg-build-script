import urllib.request
import json
import re
import urllib.parse
from pathlib import Path

def get_latest_github_tag(repo):
    # Fetch 100 tags to get a wide selection of recent releases
    url = f"https://api.github.com/repos/{repo}/tags?per_page=100"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            tags = json.loads(response.read().decode())
            valid_versions = []
            for t in tags:
                name = t['name']
                # Strip prefix 'v' or 'n' (e.g., v2.0.3 -> 2.0.3, n7.1 -> 7.1)
                clean_name = re.sub(r'^[vn]', '', name)
                # Verify it matches semantic version numbers (e.g. 2.0.3 or 8.1)
                if re.match(r'^\d+\.\d+(\.\d+)?$', clean_name):
                    valid_versions.append(clean_name)
            
            if valid_versions:
                # Sort semantically (e.g. 8.1.1 > 8.1 > 0.6.1)
                valid_versions.sort(key=lambda s: [int(x) for x in re.findall(r'\d+', s)])
                return valid_versions[-1] # Return the highest version
    except Exception as e:
        print(f"Error fetching GitHub tags for {repo}: {e}")
    return None

def get_latest_gitlab_release(repo_path):
    encoded_path = urllib.parse.quote_plus(repo_path)
    url = f"https://gitlab.com/api/v4/projects/{encoded_path}/releases?per_page=50"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            releases = json.loads(response.read().decode())
            valid_versions = []
            for r in releases:
                name = r['tag_name']
                clean_name = re.sub(r'^[vn]', '', name)
                if re.match(r'^\d+\.\d+(\.\d+)?$', clean_name):
                    valid_versions.append(clean_name)
            
            if valid_versions:
                # Sort semantically
                valid_versions.sort(key=lambda s: [int(x) for x in re.findall(r'\d+', s)])
                return valid_versions[-1] # Return the highest version
    except Exception as e:
        print(f"Error fetching GitLab releases for {repo_path}: {e}")
    return None

def main():
    script_path = Path("build-ffmpeg")
    if not script_path.exists():
        print("build-ffmpeg script not found.")
        return

    content = script_path.read_text(encoding="utf-8")
    updated = False

    # 1. Fetch latest versions
    latest_ffmpeg = get_latest_github_tag("FFmpeg/FFmpeg")
    print(f"Latest FFmpeg Version resolved: {latest_ffmpeg}")
    
    latest_svtav1 = get_latest_gitlab_release("AOMediaCodec/SVT-AV1")
    print(f"Latest SVT-AV1 Version resolved: {latest_svtav1}")

    latest_fdk = get_latest_github_tag("mstorsjo/fdk-aac")
    print(f"Latest FDK-AAC Version resolved: {latest_fdk}")

    # 2. Check and replace FFmpeg version
    if latest_ffmpeg:
        current_ffmpeg_match = re.search(r'FFMPEG_VERSION=([\d\.]+)', content)
        if current_ffmpeg_match:
            current_ffmpeg = current_ffmpeg_match.group(1)
            if current_ffmpeg != latest_ffmpeg:
                print(f"Updating FFmpeg from {current_ffmpeg} to {latest_ffmpeg}")
                content = content.replace(f"FFMPEG_VERSION={current_ffmpeg}", f"FFMPEG_VERSION={latest_ffmpeg}")
                updated = True

    # 3. Check and replace SVT-AV1 version
    if latest_svtav1:
        current_svt_match = re.search(r'if build "svtav1" "([\d\.]+)"; then', content)
        if current_svt_match:
            current_svt = current_svt_match.group(1)
            if current_svt != latest_svtav1:
                print(f"Updating SVT-AV1 from {current_svt} to {latest_svtav1}")
                content = content.replace(f'if build "svtav1" "{current_svt}"; then', f'if build "svtav1" "{latest_svtav1}"; then')
                updated = True

    # 4. Check and replace FDK-AAC version
    if latest_fdk:
        current_fdk_match = re.search(r'if build "fdk_aac" "([\d\.]+)"; then', content)
        if current_fdk_match:
            current_fdk = current_fdk_match.group(1)
            if current_fdk != latest_fdk:
                print(f"Updating FDK-AAC from {current_fdk} to {latest_fdk}")
                content = content.replace(f'if build "fdk_aac" "{current_fdk}"; then', f'if build "fdk_aac" "{latest_fdk}"; then')
                updated = True

    if updated:
        script_path.write_text(content, encoding="utf-8")
        print("Updated build-ffmpeg successfully.")
    else:
        print("All versions are up to date.")

if __name__ == "__main__":
    main()
