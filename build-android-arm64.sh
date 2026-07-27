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

TOOLCHAIN="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$HOST_TAG"

# ─── Cross-compiler tools (NOT exported globally so host tools like pkg-config
#     still compile natively with the system CC) ────────────────────────────
CROSS_CC="$TOOLCHAIN/bin/${TARGET}${API}-clang"
CROSS_CXX="$TOOLCHAIN/bin/${TARGET}${API}-clang++"
CROSS_AR="$TOOLCHAIN/bin/llvm-ar"
CROSS_LD="$TOOLCHAIN/bin/ld.lld"
CROSS_RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
CROSS_STRIP="$TOOLCHAIN/bin/llvm-strip"

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
  --ld="$CROSS_LD" \
  --ranlib="$CROSS_RANLIB" \
  --strip="$CROSS_STRIP" \
  --enable-shared \
  --disable-static \
  --enable-jni \
  --enable-mediacodec \
  --enable-libfdk-aac \
  --enable-libsvtav1 \
  --skip-install

echo "=== Copying cross-compiled ARM64 ffmpeg binary ==="
mkdir -p workspace/bin
if [ -f packages/FFmpeg-8.1.2/ffmpeg ]; then
  cp packages/FFmpeg-8.1.2/ffmpeg workspace/bin/ffmpeg
elif [ -f packages/FFmpeg-release-8.1.2/ffmpeg ]; then
  cp packages/FFmpeg-release-8.1.2/ffmpeg workspace/bin/ffmpeg
fi
find packages/ -name "ffmpeg" -type f -exec cp {} workspace/bin/ffmpeg \; 2>/dev/null || true
chmod +x workspace/bin/ffmpeg 2>/dev/null || true
echo "Build finished. Binary at workspace/bin/ffmpeg"
