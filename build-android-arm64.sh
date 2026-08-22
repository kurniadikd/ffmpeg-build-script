#!/bin/bash
# ==============================================================================
# Helper Script untuk Mengompilasi FFmpeg + SVT-AV1 + FDK-AAC untuk Android (arm64-v8a)
# ==============================================================================

set -e

if [ -z "$ANDROID_NDK_HOME" ]; then
  echo "Error: Variabel ANDROID_NDK_HOME belum diatur."
  echo "Silakan atur path NDK Anda terlebih dahulu, contoh:"
  echo "  export ANDROID_NDK_HOME=/path/to/android-ndk-r26b"
  exit 1
fi

# Clean previous build workspace to avoid contamination with x86_64 host libraries (e.g. liblcms2.a)
rm -rf workspace packages

# ─── Target Platform ────────────────────────────────────────────────────────
export API=26
export ARCH=arm64
export CPU=armv8-a
export TARGET=aarch64-linux-android
HOST_TAG=linux-x86_64

if [ ! -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$HOST_TAG" ]; then
  if [ -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64" ]; then
    HOST_TAG=darwin-x86_64
  elif [ -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/windows-x86_64" ]; then
    HOST_TAG=windows-x86_64
  fi
fi

export TOOLCHAIN="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$HOST_TAG"

# ─── Cross-compiler tools (NOT exported globally so host tools like pkg-config
#     still compile natively with the system CC) ────────────────────────────
export CROSS_CC="$TOOLCHAIN/bin/${TARGET}${API}-clang"
export CROSS_CXX="$TOOLCHAIN/bin/${TARGET}${API}-clang++"
export CROSS_AR="$TOOLCHAIN/bin/llvm-ar"
export CROSS_LD="$TOOLCHAIN/bin/ld.lld"
export CROSS_RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
export CROSS_STRIP="$TOOLCHAIN/bin/llvm-strip"

# ─── Generate Meson Cross-file for Android ARM64 ─────────────────────────────
CROSS_FILE="$(pwd)/android-arm64.ini"
cat > "$CROSS_FILE" << EOF
[binaries]
c = '$CROSS_CC'
cpp = '$CROSS_CXX'
ar = '$CROSS_AR'
ranlib = '$CROSS_RANLIB'
strip = '$CROSS_STRIP'
pkg-config = 'pkg-config'

[built-in options]
c_args = ['-fPIC', '-DANDROID', '--sysroot=$TOOLCHAIN/sysroot']
cpp_args = ['-fPIC', '-DANDROID', '--sysroot=$TOOLCHAIN/sysroot']
c_link_args = ['--sysroot=$TOOLCHAIN/sysroot']
cpp_link_args = ['--sysroot=$TOOLCHAIN/sysroot']

[properties]
sys_root = '$TOOLCHAIN/sysroot'
growing_stack = false

[build_machine]
system = 'linux'
cpu_family = 'x86_64'
cpu = 'x86_64'
endian = 'little'

[host_machine]
system = 'android'
cpu_family = 'aarch64'
cpu = 'aarch64'
endian = 'little'
EOF
export MESON_CROSS_FILE="$CROSS_FILE"

# ─── Android-specific flags (exported so FFmpeg's configure picks them up) ──
export ANDROID_BUILD=true

echo "=========================================================="
echo " Memulai Kompilasi FFmpeg Android NDK (arm64-v8a)..."
echo " Target NDK  : $ANDROID_NDK_HOME"
echo " Toolchain   : $TOOLCHAIN"
echo " Target API  : $API (Android 8.0+)"
echo " Kodek       : FDK-AAC, SVT-AV1, x264, x265, Opus, MediaCodec"
echo "=========================================================="

# ─── Jalankan build-ffmpeg dengan cross-compile flags eksplisit ─────────────
# CATATAN:
#   - CC/CXX/AR/LD TIDAK di-export agar ./configure host tools (pkg-config, dll)
#     tetap menggunakan native compiler Linux x86_64.
#   - Flag --cc / --cxx / dll diteruskan eksplisit ke build-ffmpeg → FFmpeg configure.
#   - CFLAGS/CXXFLAGS di-set via FFMPEG_EXTRA_FLAGS agar hanya berlaku untuk FFmpeg.
SKIPINSTALL=yes SKIPRAV1E=yes \
  CFLAGS="-fPIC -DANDROID" \
  CXXFLAGS="-fPIC -DANDROID" \
  ./build-ffmpeg \
  --build \
  --enable-gpl-and-non-free \
  --target-os=android \
  --arch=arm64 \
  --cpu=armv8-a \
  --enable-cross-compile \
  --cc="$CROSS_CC" \
  --cxx="$CROSS_CXX" \
  --ar="$CROSS_AR" \
  --ranlib="$CROSS_RANLIB" \
  --strip="$CROSS_STRIP" \
  --enable-shared \
  --disable-static \
  --enable-jni \
  --enable-mediacodec \
  --disable-ffplay \
  --enable-libfdk-aac \
  --enable-libsvtav1 \
  --skip-install

echo "=== Copying cross-compiled ARM64 ffmpeg binary ==="
mkdir -p workspace/bin
FFMPEG_SRC_BIN=""
for path in packages/FFmpeg-*/ffmpeg packages/FFmpeg-release-*/ffmpeg; do
  if [ -f "$path" ]; then
    FFMPEG_SRC_BIN="$path"
    break
  fi
done

if [ -n "$FFMPEG_SRC_BIN" ]; then
  cp "$FFMPEG_SRC_BIN" workspace/bin/ffmpeg
  chmod +x workspace/bin/ffmpeg
  echo "Copied $FFMPEG_SRC_BIN to workspace/bin/ffmpeg"
else
  echo "ERROR: Could not locate compiled ffmpeg binary in packages/!" >&2
  exit 1
fi

echo "=== Validating ARM64 ELF Architecture ==="
if command -v readelf >/dev/null 2>&1; then
  readelf -h workspace/bin/ffmpeg
  if ! readelf -h workspace/bin/ffmpeg | grep -qE "AArch64|183"; then
    echo "ERROR: workspace/bin/ffmpeg is NOT ARM64 (AArch64)!" >&2
    exit 1
  fi
  echo "SUCCESS: Verified workspace/bin/ffmpeg is genuine ARM64 (AArch64)!"
fi
