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


def get_latest_videolan_commit(project):
    """Get latest commit hash from code.videolan.org."""
    url = f"https://code.videolan.org/api/v4/projects/{urllib.parse.quote_plus(project)}/repository/commits?per_page=5"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            commits = json.loads(response.read().decode())
            for c in commits:
                sha = c.get("id", "")
                if len(sha) >= 8:
                    return sha
    except Exception as e:
        print(f"  Error fetching VideoLAN commits for {project}: {e}")
    return None


def get_latest_bitbucket_commit(repo):
    """Get latest commit hash from bitbucket.org."""
    url = f"https://api.bitbucket.org/2.0/repositories/{repo}/commits?pagelen=5"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            for c in data.get("values", []):
                sha = c.get("hash", "")
                if len(sha) >= 8:
                    return sha
    except Exception as e:
        print(f"  Error fetching Bitbucket commits for {repo}: {e}")
    return None


def get_latest_sourceforge(project, path="", pattern=None, major_filter=None):
    """Get latest version from SourceForge RSS feed."""
    sf_path = f"/{path}" if path else ""
    url = f"https://sourceforge.net/projects/{project}/rss?path={sf_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode()
            if pattern:
                versions = re.findall(pattern, html)
            else:
                versions = re.findall(rf'{project}-([\d]+\.[\d]+(?:\.\d+)?)\.tar', html)
            if versions:
                versions = list(set(versions))
                if major_filter:
                    versions = [v for v in versions if int(v.split(".")[0]) == major_filter]
                versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return versions[-1]
    except Exception as e:
        print(f"  Error fetching SourceForge RSS for {project}: {e}")
    return None


def get_latest_gnu_ftp(project, prefix=""):
    """Get latest version from GNU FTP directory listing."""
    url = f"https://ftp.gnu.org/gnu/{project}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode()
            pattern = rf'{project}{prefix}-([\d]+\.[\d]+(?:\.\d+)?)\.tar'
            versions = re.findall(pattern, html)
            if versions:
                versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return versions[-1]
    except Exception as e:
        print(f"  Error fetching GNU FTP for {project}: {e}")
    return None


def get_latest_nasm():
    """Get latest stable nasm version from nasm.us."""
    url = "https://www.nasm.us/pub/nasm/releasebuilds/?C=M;O=D"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode()
            # Match directory names like "3.01/" or "3.02rc9/" (skip RCs)
            versions = re.findall(r'href="(\d+\.\d+)/"', html)
            if versions:
                versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return versions[-1]
    except Exception as e:
        print(f"  Error fetching nasm version: {e}")
    return None


def get_latest_libtiff():
    """Get latest libtiff version from download.osgeo.org."""
    url = "https://download.osgeo.org/libtiff/?C=M;O=D"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode()
            versions = re.findall(r'tiff-([\d]+\.[\d]+(?:\.\d+)?)\.tar', html)
            if versions:
                versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                return versions[-1]
    except Exception as e:
        print(f"  Error fetching libtiff version: {e}")
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


def update_x264(content, new_short_hash):
    """Update x264 commit hash (short hash only, used in build line)."""
    match = re.search(r'if build "x264" "([0-9a-f]+)"', content)
    if match:
        current = match.group(1)
        if current != new_short_hash:
            print(f"  x264: {current} -> {new_short_hash}")
            content = content.replace(
                f'if build "x264" "{current}"',
                f'if build "x264" "{new_short_hash}"',
            )
            return content, True
        else:
            print(f"  x264: {current} (up to date)")
    return content, False


def update_x265(content, new_short_hash, new_full_hash):
    """Update x265 short hash in build line AND full hash in download URL."""
    changed = False
    # Update short hash in build line
    match = re.search(r'if build "x265" "([0-9a-f]+)"', content)
    if match:
        current = match.group(1)
        if current != new_short_hash:
            print(f"  x265 (build): {current} -> {new_short_hash}")
            content = content.replace(
                f'if build "x265" "{current}"',
                f'if build "x265" "{new_short_hash}"',
            )
            changed = True
        else:
            print(f"  x265 (build): {current} (up to date)")
    # Update full hash in download URL
    match = re.search(r'bitbucket\.org/multicoreware/x265_git/get/([0-9a-f]+)\.tar\.gz', content)
    if match:
        current_full = match.group(1)
        if current_full != new_full_hash:
            print(f"  x265 (url): {current_full[:8]}... -> {new_full_hash[:8]}...")
            content = content.replace(
                f'bitbucket.org/multicoreware/x265_git/get/{current_full}.tar.gz',
                f'bitbucket.org/multicoreware/x265_git/get/{new_full_hash}.tar.gz',
            )
            changed = True
    # Update filename in download command
    match = re.search(r'"x265-([0-9a-f]+)\.tar\.gz"', content)
    if match:
        current_fn = match.group(1)
        if current_fn != new_short_hash:
            content = content.replace(
                f'"x265-{current_fn}.tar.gz"',
                f'"x265-{new_short_hash}.tar.gz"',
            )
            changed = True
    return content, changed


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
        "xeve": "mpeg5/xeve",
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

    # --- x264 (VideoLAN commit hash) ---
    print("\n=== x264/x265 (commit hashes) ===")
    x264_commit = get_latest_videolan_commit("videolan/x264")
    if x264_commit:
        short = x264_commit[:8]
        content, ok = update_x264(content, short)
        if ok:
            updated_count += 1
    else:
        failed.append("x264")

    x265_commit = get_latest_bitbucket_commit("multicoreware/x265_git")
    if x265_commit:
        short = x265_commit[:7]
        content, ok = update_x265(content, short, x265_commit)
        if ok:
            updated_count += 1
    else:
        failed.append("x265")

    # --- SourceForge libraries ---
    print("\n=== SourceForge libraries ===")
    sf_libs = {
        "giflib": ("giflib", "giflib-5.x", r'giflib-([\d]+\.[\d]+(?:\.\d+)?)\.tar', 5),
        "opencore": ("opencore-amr", "opencore-amr", r'opencore-amr-([\d]+\.[\d]+(?:\.\d+)?)\.tar', None),
        "lame": ("lame", "lame", r'lame-([\d]+\.[\d]+(?:\.\d+)?)\.tar', None),
        "soxr": ("soxr", "", r'soxr-([\d]+\.[\d]+(?:\.\d+)?)', None),
        "libpng": ("libpng", "libpng16", r'libpng-([\d]+\.[\d]+(?:\.\d+)?)\.tar', None),
        "FreeType2": ("freetype", "", r'freetype-([\d]+\.[\d]+(?:\.\d+)?)\.tar', None),
    }
    for name, (project, path, pat, major) in sf_libs.items():
        latest = get_latest_sourceforge(project, path, pattern=pat, major_filter=major)
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- GNU FTP libraries ---
    print("\n=== GNU FTP libraries ===")
    gnu_libs = {
        "m4": ("m4", ""),
        "autoconf": ("autoconf", ""),
        "automake": ("automake", ""),
        "libtool": ("libtool", ""),
        "gettext": ("gettext", ""),
        "gmp": ("gmp", ""),
        "nettle": ("nettle", ""),
    }
    for name, (project, prefix) in gnu_libs.items():
        latest = get_latest_gnu_ftp(project, prefix)
        if latest:
            content, ok = update_build_version(content, name, latest)
            if ok:
                updated_count += 1
        else:
            failed.append(name)

    # --- gnutls (special GNU path) ---
    print("\n=== Other custom sources ===")
    # gnutls uses https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/
    # Check latest stable series
    try:
        url = "https://www.gnupg.org/ftp/gcrypt/gnutls/?C=M;O=D"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode()
            series = re.findall(r'v(\d+\.\d+)/', html)
            if series:
                series.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                latest_series = series[-1]
                url2 = f"https://www.gnupg.org/ftp/gcrypt/gnutls/v{latest_series}/?C=M;O=D"
                req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=30) as resp2:
                    html2 = resp2.read().decode()
                    versions = re.findall(r'gnutls-([\d]+\.[\d]+(?:\.\d+)?)\.tar', html2)
                    if versions:
                        versions.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s)])
                        latest = versions[-1]
                        content, ok = update_build_version(content, "gnutls", latest)
                        if ok:
                            updated_count += 1
    except Exception as e:
        print(f"  Error fetching gnutls: {e}")
        failed.append("gnutls")

    # nasm
    latest_nasm = get_latest_nasm()
    if latest_nasm:
        content, ok = update_build_version(content, "nasm", latest_nasm)
        if ok:
            updated_count += 1
    else:
        failed.append("nasm")

    # libtiff
    latest_tiff = get_latest_libtiff()
    if latest_tiff:
        content, ok = update_build_version(content, "libtiff", latest_tiff)
        if ok:
            updated_count += 1
    else:
        failed.append("libtiff")

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

    print("\n=== Libraries not auto-updated (no reliable API) ===")
    print("  - xvidcore: downloads.xvid.com (no version API)")
    print("  - pcre: sourceforge (EOL, 8.45 is final)")
    print("  - lv2: lv2plug.in (special version format)")
    print("  - vaapi: libva (system package)")
    print("  - vulkan: Khronos SDK versioning is complex")


if __name__ == "__main__":
    main()
