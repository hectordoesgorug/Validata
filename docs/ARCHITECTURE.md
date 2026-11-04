# Architecture Proposal

**Status: proposal for review.** This is a maintainable starting point derived from the handover and legacy assessment, not a final architecture approval.

## Proposed source layout

```text
src/validata/
├── app.py                 # composition root and application lifecycle
├── presentation/          # GUI views, dialogs, and main-thread presenters
├── application/           # use cases, job orchestration, and result policies
├── discovery/             # iterative filesystem traversal and file records
├── validation/            # dispatcher, profiles, result types, adapters
│   └── adapters/           # image, video, audio, archive, document strategies
├── counter/               # pattern inference, manual rules, consistency analysis
├── jobs/                  # cancellation, bounded work queues, worker lifecycle
├── persistence/           # settings and cache interfaces/implementations
├── logging_config.py
└── resources/             # only app-owned resources, never legacy assets
tests/
├── unit/
├── integration/
└── performance/
```

Keep the GUI as a thin presentation layer. It submits commands and renders immutable job events/results; it should not own validation rules or filesystem traversal. Application services coordinate discovery, validation, Counter, persistence, and cleanup. Domain types (file snapshot, validation profile, validation result, sequence rule, Counter finding) should not depend on Tkinter or a particular persistence library.

## GUI framework

CustomTkinter is the stated preference under consideration. It preserves a Tkinter-style event loop and can suit a compact desktop utility, but it should be compared with standard Tkinter/ttk for theme, accessibility, packaging, maintainability, and testing needs before approval. Its widget catalog does not replace `ttk.Treeview`; a mixed CTk/ttk view is likely if the Treeview remains the approved table control. Avoid adding an async framework without a demonstrated need. Keep presentation behind small interfaces so the application layer remains testable without a live window.

## Concurrency and event flow

Use one job coordinator with a producer for iterative discovery, a bounded FIFO task queue, a fixed worker pool, and a separate bounded event queue shared by producer/workers and polled by the UI thread. For each file, the scanner must: (1) discover it, (2) assign a stable job/file ID and capture a lightweight identity snapshot, (3) publish a compact `FileDiscovered` event, and only then (4) enqueue its validation task. Thus a full validation queue can pause further discovery only after the just-discovered file's row has been published. The UI can insert that row while the scanner waits for task capacity.

The bounded task queue applies backpressure when workers lag. The bounded event queue applies backpressure if the GUI falls behind; it must not become an unbounded second backlog. Queue capacities should be fixed/configurable limits measured against compact event payloads. The main thread drains events on a short scheduled tick in bounded batches and never waits on queue puts or worker joins. If a worker is blocked publishing a result because the event queue is full, the UI remains able to drain it. Use a separate small/coalesced mechanism for replaceable progress counters so progress noise cannot crowd out discovery/results. Queue ownership is explicit: the coordinator owns task admission and job counts; scanner is the only task producer; workers are task consumers and event producers; UI is the only event consumer and the only owner of Treeview mutation.

The single event queue preserves enqueue order. Since the scanner publishes `FileDiscovered` before admitting the corresponding task, a worker cannot publish that file's result before its discovery event has entered the event queue. FIFO guarantees task dequeue/dispatch order, not completion order; multiple workers can finish out of order, so results target rows by stable IDs. UI handling must tolerate cancellation/closing and stale job IDs.

At end of discovery, publish a producer-done event after all its discovery events and task admissions. The coordinator emits `JobCompleted` only after discovery is done, all accepted tasks have a terminal or explicitly not-started state, and each worker has published its final event. Because all event producers use the same FIFO event queue, the UI receives all prior row/result events before `JobCompleted`; it can then perform cleanup safely. Track accepted, queued, running, terminal, and cancelled/not-started counts under coordinator ownership. On failure, publish compact job/file error events; workers catch and report exceptions instead of silently losing tasks. Cancellation sets a shared signal, stops traversal, makes queue puts interruptible (timed puts that check cancellation), and ensures queued tasks are drained/marked not started rather than accidentally executed. Workers check cancellation before invoking adapters; active adapters use cooperative checks/timeouts and are joined off the UI thread. Completed results remain visible. Perform one completion cleanup pass on the UI thread to remove only Valid results. Leave Corrupted and all nonstandard/error/skipped results for review. Never call widget methods from worker threads or block the UI while joining workers.

For very large jobs, avoid retaining redundant full-path/task/result copies. Store compact file/job records keyed by stable IDs, expose bounded in-flight work, and measure Treeview scale and memory at 10k/50k. Progress should distinguish discovered, queued, running, completed, and not started rather than suggest one simple FIFO completion percentage.

## Validation engine and adapters

The dispatcher selects an adapter from detected category/format and passes an explicit profile plus a captured file snapshot and cancellation/time budget. Adapters return a structured result, not a boolean. The result should include classification, applied profile, method/evidence summary, timestamps, and error details safe for display/logging. Adapter code must not mutate the source.

An adapter reports **Unsupported** when no suitable check exists, **Validation Error** for tool/runtime/I/O failure, **Encrypted / Protected** when protection prevents the check, and **Incomplete / Partially readable** only when an adapter has evidence that some content is readable while integrity/completeness remains uncertain. Do not map timeouts, missing tools, access denial, or unsupported codecs to Corrupted. Profile definitions should be data-driven and versioned, but each method still needs format-specific justification and empirical evaluation.

For video, separate metadata/container inspection from packet/frame decoding. Quick may use bounded metadata/probe checks; Balanced and Thorough can increase decode coverage if performance and accuracy testing justify it. Exact mode content is an open question. Use controlled subprocess arguments, timeouts, bounded output, and reliable child-process cleanup. Treat FFprobe success as evidence of parseable metadata/streams, not proof that all media payload decodes.

## Purge boundary

Only the application service responsible for Purge should have source-file deletion capability. UI code sends an explicit confirmed Purge command containing eligible corrupted-result IDs. Capture normalized path, file size, last-write timestamp with available precision, and Windows volume identity/file ID from an open handle where available. Before deletion, reopen the path, verify it still resolves to the same file identity and compare inexpensive metadata with the validation snapshot; if changed, missing, inaccessible, or not verifiable, skip and request revalidation. A digest can provide stronger content identity only when warranted; avoid rehashing every file. To reduce the check/delete race on Windows, the Purge service should investigate opening with delete access, verifying metadata on that same handle, then requesting deletion through that handle. A path-based check immediately followed by `os.remove(path)` still has a time-of-check/time-of-use race. Keep deletion and platform-specific identity work behind the Purge boundary. Exemptions are tied to content digests and do not make non-Corrupted outcomes purgeable.

## Counter engine

Counter is independent from validation. Its input is a folder snapshot and either inferred sequence candidates or a user-defined rule. Pattern inference proposes candidate groups (shared stem, digit position/width, extension, directory scope) with confidence and examples; it should not silently choose among ambiguous patterns. Manual rules define grouping, number extraction, expected start/step, allowed extensions, treatment of gaps/duplicates/unmatched files, and recursion scope.

Analysis returns structured findings: missing numbers/ranges, duplicate numbers, inconsistent names, unexpected/unmatched files, and counts. Distinguish a count mismatch from proven missing sequence values. Keep detection deterministic and testable with tables of examples; no source files are modified.

## Persistence, logging, external tools

### Portable data location

Confirmed preference: portable mode uses settings, cache, and logs beside the executable. At startup, perform a small create/write/flush/delete probe in that directory; never assume its permissions. Proposed fallback: `%LOCALAPPDATA%\Validata\PortableFallback\<copy-id>`, where `copy-id` is a deterministic hash of the normalized executable-directory path. This isolates multiple portable copies and persists across in-place application updates. Copies in different locations have separate data; copies at the same normalized location share data. Moving a copy creates a different fallback; show the old/new locations and provide a deliberate migration action rather than silently copying/scattering data. If portable storage is writable again after fallback was selected, keep using the selected fallback until the user explicitly switches/migrates, and show its exact path in Settings/About and at startup after fallback activation. Keep a small storage-mode marker in the selected location to make subsequent launches deterministic. If `%LOCALAPPDATA%` is unavailable or unwritable, stop before starting jobs and ask the user to choose a writable location; do not silently choose another path. User approval is still needed for this fallback/migration policy. In-place executable replacement in the same directory preserves adjacent data; users should back up JSON files before manual upgrades.

Define narrow settings/cache interfaces and version their serialized schemas. A small JSON settings file and compact cache are sufficient initially; detailed persistent validation history is out of scope, so no database is proposed. Cache entries need invalidation keys that include enough file identity and validation-method/profile version to avoid reusing stale results. Logs should be useful for diagnosis without unnecessary personal path exposure; define retention and redaction policy before release. The active storage location must be visible in the UI and included in diagnostic context.

Resolve FFmpeg/FFprobe paths through a small tool manager that supports bundled and unavailable states. Keep external binaries outside Python code imports and invoke them with safe argument lists, explicit timeouts, and resource limits. Packaging owns the chosen binaries, notices, and source/compliance artifacts.

### Validation profile resolution

Persist a configurable global default profile and optional per-category override (`Video`, `Audio`, `Images`, `Archives`, `Documents`). Resolve each category as: explicit override if set, otherwise current global default. Changing the global value only changes inheriting categories. Resetting a category removes its override. Resolve once when creating each validation task and store the effective profile plus profile-definition version in the result; do not let settings changes mid-job retroactively change already dispatched tasks. Profile definitions remain proposals until format-specific checks and benchmarks are approved.

### Working results and history

The Treeview/job model is transient working state, not permanent detailed history. Keep discovered rows throughout the active job, update row status/color incrementally, and remove Valid rows in one cleanup after all work finishes. Preserve problematic/nonstandard rows and aggregate statistics for the completed in-memory job. On application exit, per-file job results need not persist. No database or permanent record of removed Valid files is required for the initial release. Future export or history features require separate approval.

## Initial format coverage proposal

Legacy extension inventory reviewed: JPEG/PNG/GIF/BMP/TIFF/WebP plus SVG/ICO/RAW/HEIC family; common video/audio containers and codecs; PDF and multiple text/office/book formats; ZIP/RAR/7z/TAR/gzip/bzip2/xz. The current legacy code itself performs materially different levels of checking, so the extension inventory is not an accuracy baseline.

Recommended staged candidates (subject to approval and representative tests):

| Group | First-release candidates | Evidence/limits |
| --- | --- | --- |
| Images | JPEG, PNG, GIF, BMP, TIFF, WebP | Decode with a maintained image library; report decoder/readability evidence, not semantic correctness. HEIC support adds a codec plug-in dependency. |
| Archives/containers | ZIP, EPUB, TAR, gzip, bzip2, xz | Full member/stream reads can surface CRC/truncation errors. EPUB adds required-package structure checks; ZIP central directory alone is insufficient. |
| Documents | PDF, TXT, CSV, XML; DOCX/ODT as ZIP containers | Parser or syntax checks only. CSV is not schema validation; XML is well-formedness only; PDF encryption/protection can block checks; office container checks do not validate application semantics. |
| Audio/video | A curated set of common FFmpeg-probe-supported extensions after tool audit | External tool required. Probe is metadata/stream inspection; stronger profiles may decode bounded packets/content after accuracy, time, and resource tests. |
| Defer pending dedicated support | SVG as renderable image, ICO, RAW camera types, DOC/PPT legacy binaries, RAR, 7z, MOBI, KPUB, PEZ | Basic byte reads are not meaningful integrity checks. Select only with suitable maintained parser/decoder and clear Unsupported behavior. |

This is an approval proposal, not a silent reduction of the confirmed multi-category product goal. Exact extensions and claims must be approved after tool/license audit and fixtures.

## Platform and packaging assessment

Confirmed target: Windows 10 x64 and Windows 11 x64. Python 3.14 documentation says Windows 10 and newer are supported; use a pinned 64-bit CPython release that is supported on both target OS versions when development begins. PyInstaller 6.22.3 supports Python 3.8+ and is built/tested per operating system, so build Windows artifacts on Windows and test the resulting bundle on both target versions. CustomTkinter documentation provides a PyInstaller packaging path requiring explicit inclusion of its theme/data directory; validate that for a one-folder then one-file build. Python’s Tkinter/ttk provides the Treeview control, while CustomTkinter is a wrapper; use CTk for shell controls and ttk Treeview if the UI decision stands. Keep core validation/Counter free of Windows path/UI assumptions; isolate Windows file-identity and portable-path facilities behind adapters. References: [Python Windows support](https://docs.python.org/3/using/windows.html), [PyInstaller manual](https://pyinstaller.org/en/stable/), [CustomTkinter packaging](https://customtkinter.tomschimansky.com/documentation/packaging/).

Lifecycle risk: Microsoft ended support for standard Windows 10 Home/Pro on October 14, 2025. Application compatibility can remain a target, but the project should decide whether it supports Windows 10 editions enrolled in ESU or LTSC only, or merely provides best-effort compatibility for unserviced Windows 10. Do not describe an unserviced OS as currently supported by Microsoft. [Microsoft Windows 10 lifecycle](https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro).

## Supplied binary and icon audit status

Both supplied executables run and identify as **FFmpeg/FFprobe 8.0 essentials_build-www.gyan.dev**, compiled with GCC 15.2.0. Reported library versions and configure strings match. Libraries: libavutil 60.8.100, libavcodec 62.11.100, libavformat 62.3.100, libavdevice 62.3.100, libavfilter 11.4.100, libswscale 9.1.100, and libswresample 6.1.100. The exact reported configuration is:

```text
--enable-gpl --enable-version3 --enable-static --disable-w32threads --disable-autodetect
--enable-fontconfig --enable-iconv --enable-gnutls --enable-libxml2 --enable-gmp
--enable-bzlib --enable-lzma --enable-zlib --enable-libsrt --enable-libssh --enable-libzmq
--enable-avisynth --enable-sdl2 --enable-libwebp --enable-libx264 --enable-libx265
--enable-libxvid --enable-libaom --enable-libopenjpeg --enable-libvpx --enable-mediafoundation
--enable-libass --enable-libfreetype --enable-libfribidi --enable-libharfbuzz --enable-libvidstab
--enable-libvmaf --enable-libzimg --enable-amf --enable-cuda-llvm --enable-cuvid --enable-dxva2
--enable-d3d11va --enable-d3d12va --enable-ffnvcodec --enable-libvpl --enable-nvdec --enable-nvenc
--enable-vaapi --enable-openal --enable-libgme --enable-libopenmpt --enable-libopencore-amrwb
--enable-libmp3lame --enable-libtheora --enable-libvo-amrwbenc --enable-libgsm
--enable-libopencore-amrnb --enable-libopus --enable-libspeex --enable-libvorbis --enable-librubberband
```

It enables `--enable-gpl --enable-version3 --enable-static`, and neither tool enables `--enable-nonfree`. This identifies an FFmpeg GPLv3 build, consistent with Gyan's statement that its builds are 64-bit, static, and GPLv3. Both PE files have machine type `0x8664` (x64). SHA-256 fingerprints are recorded in the decision log. The configure string includes common media libraries (including libx264, libx265, libvpx, libaom, libmp3lame, libopus, and libvorbis); decoder/demuxer listings include H.264, HEVC, AV1, VP9, MPEG-2/4, ProRes, AAC, MP3, Opus, FLAC, Vorbis, WMA, MP4/MOV, Matroska/WebM, AVI, MPEG-TS, WAV, and Ogg. These are technically suitable candidates for probe/decode-based media validation, subject to real-file accuracy, performance, and Windows 10/11 testing. They do not imply that an FFprobe stream listing proves complete decode or integrity. FFmpeg 9.0.2 was the latest stable upstream release at this audit date; evaluate the current supported release before shipping and rerun these compatibility, license, and codec checks.

The matching embedded version/configuration and library versions indicate the two tools are companion binaries from the same build family; this is not cryptographic proof of archive provenance. Both are verified x64 PE files. Gyan describes its Windows builds as Windows 10 or later, which aligns with the target OS floor; still test the selected release on both Windows 10 and 11. [Gyan FFmpeg build information](https://www.gyan.dev/ffmpeg/builds/).

**Licensing is a material release blocker until resolved.** `--enable-gpl --enable-version3` activates GPL components and version 3 licensing; the included libx264/libx265 and static linking make this unsuitable to treat as an LGPL-only drop-in. Do not distribute these binaries inside Validata until the project license and distribution model are approved and GPLv3 obligations are met. Preserve the exact corresponding FFmpeg and included-library source, build/configuration materials, notices, and any required written offer/source access for the distributed binary. FFmpeg's upstream guide requires checking build flags and corresponding source; Gyan labels these static builds GPLv3. A legal review should assess how distributing the separate GPL command-line programs alongside Validata affects the application licensing, and codec patent considerations separately. No conclusion here is legal advice. [FFmpeg license guidance](https://ffmpeg.org/legal.html).

The user-supplied `assets/icon.png` is a readable, visually inspected 1024×1024 PNG, suitable as GUI artwork/source artwork when scaled. `assets/icon.ico` has a valid directory with six in-bounds image payloads at 16, 32, 48, 64, 128, and 256 pixels and opens successfully with the Windows icon decoder; suitable for the Windows executable/window icon. Both were left unchanged.

## Proposed directory growth

Add code, tests, CI, and packaging configuration only after architecture and unresolved product choices are approved. A Python package under `src/` is proposed to reduce accidental imports from the repository root. No legacy source or assets should be brought into this tree.
