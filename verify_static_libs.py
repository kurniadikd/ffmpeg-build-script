#!/usr/bin/env python3
import os
import sys
import shutil

def verify(workspace_dir, configure_options):
    print("=== STARTING STATIC LIBRARY SANITY CHECK ===")
    lib_dir = os.path.join(workspace_dir, "lib")
    pkgconfig_dir = os.path.join(lib_dir, "pkgconfig")
    
    # 1. Resolve known Windows library naming quirks
    # xvidcore.a -> libxvidcore.a
    xvid_a = os.path.join(lib_dir, "xvidcore.a")
    libxvid_a = os.path.join(lib_dir, "libxvidcore.a")
    if os.path.exists(xvid_a) and not os.path.exists(libxvid_a):
        print(f"[FIX] Copying {xvid_a} -> {libxvid_a} for linker compat...")
        shutil.copy2(xvid_a, libxvid_a)

    # 2. Unconditionally patch libzmq.pc if it exists
    zmq_pc = os.path.join(pkgconfig_dir, "libzmq.pc")
    if os.path.exists(zmq_pc):
        print(f"[FIX] Inspecting and patching {zmq_pc} for Windows static linking...")
        with open(zmq_pc, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        patched = False
        new_lines = []
        for line in lines:
            # Add -DZMQ_STATIC if not present
            if line.startswith("Cflags:") and "-DZMQ_STATIC" not in line:
                line = line.strip() + " -DZMQ_STATIC\n"
                patched = True
            # Add -lws2_32 if not present
            if line.startswith("Libs:") and "-lws2_32" not in line:
                line = line.strip() + " -lws2_32\n"
                patched = True
            new_lines.append(line)
            
        if patched:
            with open(zmq_pc, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print("[FIX] Successfully patched libzmq.pc Cflags and Libs.")
        else:
            print("[INFO] libzmq.pc is already patched.")

    # 3. Map FFmpeg configure options to expected static library files
    lib_mappings = {
        "--enable-libx264": ["libx264.a"],
        "--enable-libx265": ["libx265.a"],
        "--enable-libzmq": ["libzmq.a"],
        "--enable-libxvid": ["libxvidcore.a"],
        "--enable-libvmaf": ["libvmaf.a"],
        "--enable-libmp3lame": ["libmp3lame.a"],
        "--enable-libopus": ["libopus.a"],
        "--enable-libwebp": ["libwebp.a", "libwebpmux.a"],
        "--enable-libjxl": ["libjxl.a", "libjxl_threads.a"],
        "--enable-libxeve": ["libxeve.a"],
        "--enable-libxevd": ["libxevd.a"],
        "--enable-libxml2": ["libxml2.a"],
        "--enable-libzimg": ["libzimg.a"],
        "--enable-liblcms2": ["liblcms2.a"],
        "--enable-libfreetype": ["libfreetype.a"],
        "--enable-libfribidi": ["libfribidi.a"],
        "--enable-libharfbuzz": ["libharfbuzz.a"],
        "--enable-libfontconfig": ["libfontconfig.a"],
        "--enable-libass": ["libass.a"],
        "--enable-libdav1d": ["libdav1d.a"],
        "--enable-libsvtav1": ["libSvtAv1Enc.a"],
        "--enable-libsvthevc": ["libSvtHevcEnc.a"],
        "--enable-libsvtvp9": ["libSvtVp9Enc.a"],
        "--enable-liblc3": ["liblc3.a"],
        "--enable-libsrt": ["libsrt.a"],
    }

    missing_libs = []
    
    print("\n[INFO] Checking enabled external libraries:")
    for option in configure_options:
        if option in lib_mappings:
            expected_files = lib_mappings[option]
            found_all = True
            for f in expected_files:
                f_path = os.path.join(lib_dir, f)
                if not os.path.exists(f_path):
                    print(f"  [ERROR] {option} is enabled, but missing: {f_path}")
                    missing_libs.append(f)
                    found_all = False
            if found_all:
                print(f"  [OK] {option} -> {', '.join(expected_files)}")

    print("\n=== SANITY CHECK RESULTS ===")
    if missing_libs:
        print(f"[FATAL] Missing {len(missing_libs)} static library files! FFmpeg configure WILL fail.")
        print("Please check the build logs of the packages above.")
        return False
    else:
        print("[SUCCESS] All enabled static library files are present in the workspace.")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: verify_static_libs.py <workspace_dir> [configure_options...]")
        sys.exit(1)
        
    workspace = sys.argv[1]
    options = sys.argv[2:]
    
    success = verify(workspace, options)
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)
