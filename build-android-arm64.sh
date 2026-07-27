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

export API=26
export ARCH=arm64
export CPU=armv8-a
export TARGET=aarch64-linux-android
export HOST_TAG=linux-x86_64

if [ ! -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$HOST_TAG" ]; then
  if [ -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64" ]; then
    export HOST_TAG=darwin-x86_64
  elif [ -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/windows-x86_64" ]; then
    export HOST_TAG=windows-x86_64
  fi
fi

export TOOLCHAIN=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$HOST_TAG

export CC=$TOOLCHAIN/bin/${TARGET}${API}-clang
export CXX=$TOOLCHAIN/bin/${TARGET}${API}-clang++
export AR=$TOOLCHAIN/bin/llvm-ar
export LD=$TOOLCHAIN/bin/ld.lld
export RANLIB=$TOOLCHAIN/bin/llvm-ranlib
export STRIP=$TOOLCHAIN/bin/llvm-strip

export ANDROID_BUILD=true
export CFLAGS="-fPIC -DANDROID"
export CXXFLAGS="-fPIC -DANDROID"

echo "=========================================================="
echo " Memulai Kompilasi FFmpeg Android NDK (arm64-v8a)..."
echo " Target NDK: $ANDROID_NDK_HOME"
echo " Target API: $API (Android 8.0+)"
echo " Kodek: FDK-AAC, SVT-AV1, x264, x265, Opus, MediaCodec"
echo "=========================================================="

SKIPINSTALL=yes SKIPRAV1E=yes ./build-ffmpeg \
  --build \
  --enable-gpl-and-non-free \
  --target-os=android \
  --arch=arm64 \
  --cpu=armv8-a \
  --enable-cross-compile \
  --cc="$CC" \
  --cxx="$CXX" \
  --ar="$AR" \
  --ld="$LD" \
  --ranlib="$RANLIB" \
  --strip="$STRIP" \
  --enable-shared \
  --disable-static \
  --enable-jni \
  --enable-mediacodec \
  --enable-libfdk-aac \
  --enable-libsvtav1 \
  --skip-install
