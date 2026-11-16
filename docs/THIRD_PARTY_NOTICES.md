# Third-Party Notices and Licensing Record

**Status: owner-managed dependency policy approved for v1.0.0.** Validata will not download, bundle, or redistribute FFmpeg/FFprobe. This document records the separately licensed development binaries and their audit history; it is not legal advice.

## Validata source license

Validata source code is licensed under the **MIT License**, copyright (c) 2026 hectordoesgorug; see the root [LICENSE](../LICENSE). This does not change the separate license of third-party executables.

## FFmpeg and FFprobe baseline

| Property | Verified value |
| --- | --- |
| Programs | `ffmpeg.exe`, `ffprobe.exe` |
| Version/build ID | `9.0.2-essentials_build-www.gyan.dev` |
| Provider | Gyan.dev; exact source archive provenance not independently verified |
| Release date listed by Gyan | 2026-09-19 |
| Compiler | GCC 16.2.0 (Rev3, MSYS2 project) |
| Architecture | Both are valid Windows PE x64 (`0x8664`) |
| Linking / license flags | Static; `--enable-gpl --enable-version3`; no `--enable-nonfree` observed |
| FFmpeg library versions | libavutil 61.1.102; libavcodec 63.1.102; libavformat 63.1.102; libavdevice 63.1.102; libavfilter 12.1.102; libswscale 10.1.102; libswresample 7.1.102 |
| FFmpeg SHA-256 | `3256173f3f8bffd7df12227c68adf68025edb1832273a9530688a7bb1ed8edec` |
| FFprobe SHA-256 | `f0d36ecbbdd3bcfac3efa078c96c7271c2e68b3810595552ac3b7f17e9a65c52` |

The hashes above were recalculated locally with Windows `certutil -hashfile` and match the values supplied by the owner. They identify the current files; they have **not** been matched to a publisher checksum for the extracted executables and must not be described as publisher-verified checksums.

### Configure flags reported by the executables

```text
--enable-gpl --enable-version3 --enable-static --disable-w32threads --disable-autodetect
--enable-cairo --enable-fontconfig --enable-iconv --enable-gnutls --enable-libxml2 --enable-gmp
--enable-bzlib --enable-lzma --enable-zlib --enable-libsrt --enable-libssh --enable-libzmq
--enable-avisynth --enable-sdl2 --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxvid
--enable-libaom --enable-libopenjpeg --enable-libvpx --enable-mediafoundation --enable-libass
--enable-libfreetype --enable-libfribidi --enable-libharfbuzz --enable-libvidstab --enable-libvmaf
--enable-libzimg --enable-amf --enable-cuda-llvm --enable-cuvid --enable-dxva2 --enable-d3d11va
--enable-d3d12va --enable-ffnvcodec --enable-libvpl --enable-nvdec --enable-nvenc --enable-vaapi
--enable-openal --enable-libgme --enable-libopenmpt --enable-libopencore-amrwb --enable-libmp3lame
--enable-libtheora --enable-libvo-amrwbenc --enable-libgsm --enable-libopencore-amrnb
--enable-libopus --enable-libspeex --enable-libvorbis --enable-librubberband
```

Both executables reported the same version, build identifier, compiler, configuration, and library versions. `-L` reports the GNU General Public License. Decoder/demuxer listings include common audio/video families such as H.264, HEVC, AV1, VP9, MPEG-2/4, ProRes, AAC, MP3, Opus, FLAC, Vorbis, WMA, MP4/MOV, Matroska/WebM, AVI, MPEG-TS, WAV, and Ogg. This is a capability inventory, not a guarantee that every file using those extensions or codecs can be completely decoded or validated.

## Upstream sources and provenance

Gyan lists the 9.0.2 Essentials package as its release build dated 2026-09-19 and links the FFmpeg source revision [`946fcce07b`](https://github.com/FFmpeg/FFmpeg/commit/946fcce07b). Gyan describes its Windows builds as 64-bit, static, and GPLv3, and lists the external libraries in the Essentials variant. The FFmpeg upstream licensing page explains that GPL-enabled components change the license applicable to FFmpeg; the build's `--enable-gpl --enable-version3` flags and Gyan's classification agree that this is a GPLv3 build. It is not an LGPL-only build.

Sources: [Gyan build/download page](https://www.gyan.dev/ffmpeg/builds/), [Gyan 9.0.2 release mirror](https://github.com/GyanD/codexffmpeg/releases/tag/9.0.2), [FFmpeg source revision for 9.0.2](https://github.com/FFmpeg/FFmpeg/commit/946fcce07b), [FFmpeg license guidance](https://ffmpeg.org/legal.html), and [GNU GPL version 3](https://www.gnu.org/licenses/gpl-3.0.html).

The supplied local files were inspected in place and remain untouched/ignored. Their embedded version string and matching configuration are consistent with Gyan's 9.0.2 Essentials build, but do not prove which archive they came from. The archive, its README/license files, publisher checksum, exact external-library source revisions, and exact build scripts have not been retained or independently checked here. They are development-only tools. If a future release proposes bundling or redistributing FFmpeg, separately obtain owner approval and review the exact corresponding source, dependency notices, configuration, build scripts, and legal obligations before making that change.

## Licensing obligations and interpretation

**Confirmed from the observed build and upstream notices:** this is a static, GPLv3-configured FFmpeg build. `--enable-nonfree` is absent. Gyan labels its static builds GPLv3. The enabled external libraries include libx264, libx265, libxvid, libaom, libopenjpeg, libvpx, libmp3lame, libopus, libvorbis, libspeex, and others; each dependency's notice and license must be inventoried rather than assumed to be covered solely by one FFmpeg notice.

When conveying GPLv3 object code, GPLv3 section 6 requires providing the Corresponding Source using one of its allowed methods, and sections 4–5 address notices, license text, and conveying modified/source forms. For this exact static build, prepare the matching FFmpeg source, sources for included components to the extent required by their licenses, applicable license texts and notices, and reproducible build/configuration materials or a compliant written/network source offer. Preserve copyright, warranty, and license notices from the exact package and enabled third-party libraries; identify FFmpeg 9.0.2, the Gyan Essentials build, and the source location in release notices. Do not assume the LGPL-specific sample notice on FFmpeg's legal page is the complete notice set for this GPLv3 build. The precise delivery mechanism and coverage should be checked against the actual source archive and by counsel. FFmpeg's LGPL checklist is not a substitute here because this build enables GPL components and is static.

GPLv3 section 5 says inclusion of a covered program in an aggregate does not by itself apply GPL terms to the other separate works. Validata calls FFmpeg as a separate command-line process, but whether a particular integration/distribution is a mere aggregate or forms a combined work is a legal interpretation. Keep Validata's MIT source and the FFmpeg executables separately identified, licensed, and noticed; obtain legal review before claiming the MIT application is unaffected by a release configuration.

PyInstaller one-file mode places bundled support files inside one executable and extracts them to a temporary directory at runtime. This is recorded only for future packaging review: the approved v1.0.0 policy excludes FFmpeg/FFprobe from all bundles and release artifacts. If a future owner-approved proposal changes that policy, packaging mechanics do not remove licensing/source obligations, and the exact integration and compliance approach must be reviewed before release. [PyInstaller one-file operation](https://pyinstaller.org/en/stable/operating-mode.html).

## Approved v1.0.0 dependency policy

FFmpeg/FFprobe are optional, user-managed tools. The application will provide the [Gyan download page](https://www.gyan.dev/ffmpeg/builds/), let users choose the folder containing both executables, check availability/version/compatibility, and persist their paths. No automatic download/install in v1.0.0. Do not put either binary in Git, PyInstaller bundles, portable ZIPs, or GitHub Releases. When a tool is unavailable, preserve checks that do not require it and report why dependent checks did not run; missing tools are not proof of corruption and must not yield a silent Valid result. The owner supplied the current local binaries solely as the development baseline; `.gitignore` excludes them.

Any future proposal to distribute FFmpeg requires explicit owner approval and a separate licensing/source/notice review. The MIT license applies to Validata source only, not to these external tools.

## Application icon assets

The owner confirms `assets/icon.ico` and `assets/icon.png` were generated using ChatGPT and approves them for Validata branding. Both are tracked. The ICO opens with Windows icon decoding; the PNG opens as 1024×1024. Do not claim independently verified originality or copyright protection.
