import urllib.request
import json
import re
import urllib.parse
import os
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def github_headers():
    headers = {"User-Agent": "Mozilla/5.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def get_latest_github_tag(repo, prefix="v", major_filter=None):
    url = f"https://api.github.com/repos/{repo}/tags?per_page=100"
    req = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            tags = json.loads(response.read().decode())
            valid = []
            for t in tags:
                name = t["name"]
                clean = name[len(prefix):] if prefix and name.startswith(prefix) else name
                if re.match(r"^\d+\.\d+(\.\d+)?$", clean):
                    if major_filter:
                        major = int(clean.split(".")[0])
                        if major != major_filter:
                            continue
                    valid.append(clean)
            if valid:
                valid.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return valid[-1]
    except Exception as e:
        print(f"  Error fetching GitHub tags for {repo}: {e}")
    return None


def get_latest_gitlab_release(repo_path):
    encoded = urllib.parse.quote_plus(repo_path)
    url = f"https://gitlab.com/api/v4/projects/{encoded}/releases?per_page=50"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            releases = json.loads(response.read().decode())
            valid = []
            for r in releases:
                clean = re.sub(r"^[vn]", "", r["tag_name"])
                if re.match(r"^\d+\.\d+(\.\d+)?$", clean):
                    valid.append(clean)
            if valid:
                valid.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return valid[-1]
    except Exception as e:
        print(f"  Error fetching GitLab releases for {repo_path}: {e}")
    return None


def get_latest_gitlab_tags(repo_path):
    encoded = urllib.parse.quote_plus(repo_path)
    url = f"https://gitlab.com/api/v4/projects/{encoded}/repository/tags?per_page=50"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            tags = json.loads(response.read().decode())
            valid = []
            for t in tags:
                clean = re.sub(r"^[vn]", "", t["name"])
                if re.match(r"^\d+\.\d+(\.\d+)?$", clean):
                    valid.append(clean)
            if valid:
                valid.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return valid[-1]
    except Exception as e:
        print(f"  Error fetching GitLab tags for {repo_path}: {e}")
    return None


def get_latest_xiph(project):
    url = f"https://downloads.xiph.org/releases/{project}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode()
            versions = re.findall(rf"{project}-([\d]+\.[\d]+(?:\.\d+)?)\.tar", html)
            if versions:
                versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return versions[-1]
    except Exception as e:
        print(f"  Error fetching Xiph releases for {project}: {e}")
    return None


def get_latest_videolan(project):
    url = f"https://code.videolan.org/api/v4/projects/{urllib.parse.quote_plus(project)}/repository/tags?per_page=50"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            tags = json.loads(response.read().decode())
            valid = []
            for t in tags:
                clean = re.sub(r"^[vn]", "", t["name"])
                if re.match(r"^\d+\.\d+(\.\d+)?$", clean):
                    valid.append(clean)
            if valid:
                valid.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return valid[-1]
    except Exception as e:
        print(f"  Error fetching VideoLAN tags for {project}: {e}")
    return None


def get_latest_aom_from_gcs():
    url = "https://storage.googleapis.com/aom-releases/?max-keys=200"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            xml = response.read().decode()
            versions = re.findall(r"libaom-([\d]+\.[\d]+(?:\.\d+)?)\.tar\.gz", xml)
            if versions:
                versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return versions[-1]
    except Exception as e:
        print(f"  Error fetching AOM releases from GCS: {e}")
    return None


def update_build_version(content, build_name, new_version):
    match = re.search(rf'if build "{re.escape(build_name)}" "([^"]+)"', content)
    if match:
        current = match.group(1)
        if current != new_version:
            print(f"  {build_name}: {current} -> {new_version}")
            content = content.replace(
                f'if build "{build_name}" "{current}"',
                f'if build "{build_name}" "{new_version}"',
            )
            return content, True
        else:
            print(f"  {build_name}: {current} (up to date)")
    return content, False


def main():
    script_path = Path("build-ffmpeg")
    if not script_path.exists():
        print("build-ffmpeg script not found.")
        return

    content = script_path.read_text(encoding="utf-8")
    updated_count = 0
    failed = []

    # --- FFmpeg ---
    print("=== FFmpeg ===")
    latest = get_latest_github_tag("FFmpeg/FFmpeg", prefix="n")
    if latest:
        m = re.search(r"FFMPEG_VERSION=([\d\.]+)", content)
        if m:
            current = m.group(1)
            if current != latest:
                print(f"  FFmpeg: {current} -> {latest}")
                content = content.replace(f"FFMPEG_VERSION={current}", f"FFMPEG_VERSION={latest}")
                updated_count += 1
            else:
                print(f"  FFmpeg: {current} (up to date)")
    else:
        failed.append("FFmpeg")

    # --- GitHub repos (v-prefix semver) ---
    print("\n=== GitHub repos (v-prefix) ===")
    github_v = {
        "yasm": "yasm/yasm",
        "zlib": "madler/zlib",
        "cmake": "Kitware/CMake",
        "rav1e": "xiph/rav1e",
        "libvpx": "webmproject/libvpx",
        "vid_stab": "georgmartius/vid.stab",
        "libvmaf": "Netflix/vmaf",
        "svthevc": "OpenVisualCloud/SVT-HEVC",
        "libjxl": "libjxl/libjxl",
        "srt": "Haivision/srt",
        "zvbi": "zapping-vbi/zvbi",
        "libzmq": "zeromq/libzmq",
        "amf": "GPUOpen-LibrariesAndSDKs/AMF",
        "OpenCL-Headers": "KhronosGroup/OpenCL-Headers",
        "OpenCL-ICD-Loader": "KhronosGroup/OpenCL-ICD-Loader",
        "fdk_aac": "mstorsjo/fdk-aac",
    }
    for name, repo in github_v.items():
        latest = get_latest_github_tag(repo, prefix="v")
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- GitHub repos (special tag prefixes) ---
    print("\n=== GitHub repos (special prefixes) ===")
    github_special = {
        "openssl": ("openssl/openssl", "openssl-", None),
        "nv-codec": ("FFmpeg/nv-codec-headers", "n", None),
        "libsdl": ("libsdl-org/SDL", "release-", 2),
        "Vulkan-Headers": ("KhronosGroup/Vulkan-Headers", "vulkan-sdk-", None),
        "zimg": ("sekrit-twc/zimg", "release-", None),
        "lcms2": ("mm2/Little-CMS", "lcms", None),
        "glslang": ("KhronosGroup/glslang", "", None),
        "vapoursynth": ("vapoursynth/vapoursynth", "R", None),
    }
    for name, (repo, prefix, major) in github_special.items():
        latest = get_latest_github_tag(repo, prefix=prefix, major_filter=major)
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- GitLab repos ---
    print("\n=== GitLab repos ===")
    gitlab_repos = {
        "svtav1": "AOMediaCodec/SVT-AV1",
        "serd": "drobilla/serd",
        "sord": "drobilla/sord",
        "sratom": "lv2/sratom",
        "lilv": "lv2/lilv",
        "zix": "drobilla/zix",
    }
    for name, repo in gitlab_repos.items():
        latest = get_latest_gitlab_release(repo)
        if not latest:
            latest = get_latest_gitlab_tags(repo)
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- VideoLAN repos ---
    print("\n=== VideoLAN repos ===")
    videolan = {"dav1d": "videolan/dav1d"}
    for name, repo in videolan.items():
        latest = get_latest_videolan(repo)
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- Xiph.org repos ---
    print("\n=== Xiph.org repos ===")
    xiph = {
        "opus": "opus",
        "libogg": "ogg",
        "libvorbis": "vorbis",
        "libtheora": "theora",
    }
    for name, project in xiph.items():
        latest = get_latest_xiph(project)
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- libaom (Google Cloud Storage) ---
    print("\n=== Google Cloud Storage ===")
    latest_aom = get_latest_aom_from_gcs()
    if latest_aom:
        content, ok = update_build_version(content, "av1", latest_aom)
        if ok:
            updated_count += 1
    else:
        failed.append("av1 (libaom)")

    # --- Summary ---
    print("\n=== Summary ===")
    if updated_count > 0:
        script_path.write_text(content, encoding="utf-8")
        print(f"Updated {updated_count} library(ies) successfully.")
    else:
        print("All versions are up to date.")

    if failed:
        print(f"\nCould not check: {', '.join(failed)}")
        print("(These may need manual version checks)")

    print("\n=== Libraries with commit-hash versions (manual update only) ===")
    print("  - x264: commit hash (code.videolan.org)")
    print("  - x265: commit hash (bitbucket.org)")

    print("\n=== Libraries from FTP/SourceForge (manual update only) ===")
    print("  - nasm: nasm.us")
    print("  - xvidcore: downloads.xvid.com")
    print("  - giflib: sourceforge")
    print("  - pcre: sourceforge (EOL, 8.45 is final)")
    print("  - opencore-amr: sourceforge")
    print("  - lame: sourceforge")
    print("  - soxr: sourceforge")
    print("  - libpng: sourceforge")
    print("  - FreeType2: sourceforge")
    print("  - libtiff: download.osgeo.org")
    print("  - gettext/gmp/nettle/gnutls: GNU FTP")
    print("  - lv2: lv2plug.in")
    print("  - vaapi: libva (system package)")
    print("  - m4/autoconf/automake/libtool: GNU FTP")


if __name__ == "__main__":
    main()
