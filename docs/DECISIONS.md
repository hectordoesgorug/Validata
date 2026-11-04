# Decisions and Proposals

This log separates handover-confirmed direction from recommendations that still need approval. No architecture proposal below changes a confirmed requirement.

## Confirmed by the Validata handover

- Validata is a greenfield Python desktop application; the legacy Bulk Media Validator is read-only reference material.
- Validator and Counter are equally important primary capabilities.
- Discovery and validation should progress concurrently, dispatch through FIFO work queues, and update the GUI only on its main thread.
- Quick, Balanced, and Thorough are the named profiles; Balanced is the proposed default. Inheritance behavior is confirmed; exact checks remain undecided.
- Ordinary operations do not modify source files. Purge is the sole permitted deletion path and is limited to genuinely Corrupted results.
- The eventual deployment target is a self-contained portable Windows executable with persistent settings/cache and no required administrator privileges.
- Initial OS target is 64-bit Windows 10 and Windows 11.
- Portable mode uses the executable directory for settings, cache, and logs when writable. It must not assume write access and must show the active storage location.
- Profile inheritance is defined: each category without an override inherits the global default; changing the global default preserves explicit overrides; each category can reset to inherit; results record the effective profile; profile definitions are versioned.
- Validation results are transient job state. Keep active rows visible, remove Valid rows after job completion, retain problematic/nonstandard rows and aggregate statistics. Persistent per-file validation history and a database are outside initial-release scope.
- Do not implement Validator or Counter during the foundation assignment; do not push the initial documentation without review and approval.

## Technical recommendations — approval needed

| ID | Recommendation | Rationale | Status |
| --- | --- | --- | --- |
| PROP-001 | Organize implementation as a `src/validata` package with separate presentation, application, discovery, validation adapters, Counter, jobs, and persistence modules. | Enforces boundaries and allows domain logic to be tested without the GUI. | Proposed |
| PROP-002 | Use one producer, a bounded FIFO task queue, a fixed worker pool, and a separate bounded event queue polled by the UI thread. Publish each `FileDiscovered` event before attempting task-queue admission; coalesce progress events. | Makes each found file available for row insertion before queue backpressure, while bounding both work and event memory. | Proposed |
| PROP-003 | Model outcomes as structured classifications with evidence and profile metadata; never conflate environmental/tool failures with corruption. | Prevents false positive deletion and supports inspection of nonstandard results. | Proposed |
| PROP-004 | Make Counter infer candidates with confidence and require manual rules for ambiguous patterns. | Avoids silently treating unrelated names or files as one sequence. | Proposed |
| PROP-005 | Revalidate captured file identity before Purge and skip changed/unavailable files. | Reduces stale-result deletion risk. | Proposed |
| PROP-006 | Keep CustomTkinter under evaluation against Tkinter/ttk before choosing the UI dependency. | Framework preference is known; trade-offs and packaging fit remain unassessed. | Proposed |
| PROP-007 | Build a one-folder PyInstaller development artifact first and a one-file release artifact only after runtime-data and FFmpeg handling are validated. | Easier diagnosis during development; one-file mode extracts bundled resources at runtime and needs careful path/licensing handling. | Proposed |
| PROP-008 | Use the executable directory for persistent portable data when writable; otherwise use a deterministic per-copy fallback under `%LOCALAPPDATA%\Validata\PortableFallback`. Keep the active location visible and do not silently migrate. | Honors portable preference, handles read-only directories, and isolates copies; exact migration UX still needs approval. | Proposed |
| PROP-009 | Stage initial format coverage by evidence and tooling; do not treat the legacy extension list as automatic v1 scope. | Some legacy paths only read a small prefix or cannot validate the format meaningfully. | Recommendation for approval |
| PROP-010 | Build one-folder with PyInstaller first; test a one-file release build on Windows 10/11. Include CustomTkinter data explicitly if selected. | PyInstaller packaging is platform-specific, and CTk documents additional theme/data collection. | Proposed |
| PROP-011 | Do not bundle the supplied FFmpeg binaries unless the GPLv3 implications are compatible with the approved Validata license and required source/notices are available. | The observed build flags enable GPL and version 3; the binaries are static and include GPL codec libraries. | Release blocker / approval needed |

## Initial repository observations

At assignment start, the Validata directory contained zero entries and had no Git repository metadata. Consequently there was no existing branch, history, or configured remote to inspect. The intended remote URL is recorded in the handover, but network retrieval of that GitHub page was unavailable during this inspection; remote ownership/content could not be independently verified. This documentation commit initializes local history only and does not push.

The legacy directory was readable for reference, but querying its Git status was denied by the environment. Its working-tree/repository state therefore remains unverified. No legacy files were modified.

## Handover 1.1 technical audit

- FFmpeg and FFprobe both identify as `8.0-essentials_build-www.gyan.dev`, GCC 15.2.0. Their reported configure strings and library versions match. Both enable GPL, version 3, and static linking; neither enables nonfree. The build includes common audio/video libraries and decoders/demuxers relevant to candidate coverage. This suggests companion binaries from the same build family, though provenance is not cryptographically verified.
- Local SHA-256: `ffmpeg.exe` = `1FCB0CB525085CC5BE3AD4BE16799D60786B65CC36951622A018D00F78C0FB5D`; `ffprobe.exe` = `DD315AE1B6575220F9A503343D68E55983B5BF966A43C63874F3C646DC83742F`.
- Gyan describes its Windows builds as static GPLv3, and these build flags include `--enable-gpl --enable-version3`, including libx264/libx265. Project licensing and GPL source/notices arrangements must be resolved before redistribution. See [Architecture: binary audit](ARCHITECTURE.md#supplied-binary-and-icon-audit-status).
- `assets/icon.png` is a readable/visually inspected 1024×1024 PNG. `assets/icon.ico` has six bounded icon images (16–256 px) and opened successfully in the Windows icon decoder. Both are appropriate in roles documented in Architecture; both remain unchanged and uncommitted.
- Standard Windows 10 Home/Pro ended support October 14, 2025. Keep Windows 10 x64 as the confirmed application compatibility target, but clarify what edition/build support promise is intended. FFmpeg 9.0.2 was the latest stable upstream release at this audit date, so the supplied FFmpeg 8.0 pair should be treated as audit samples and reevaluated before release.
- `.gitignore` excludes root-level FFmpeg executables and generated stress fixtures. It does not ignore `assets/` or documentation. The FFmpeg files are now ignored and must not be committed; icons remain untracked user assets.

## Decisions still open

See [Requirements: Open questions](REQUIREMENTS.md#open-questions). In particular, exact profile checks, initial format coverage, sequence grammar, fallback/migration behavior, Windows 10 supported editions policy, project license, and FFmpeg source/compliance need decisions before corresponding implementation or release work.
