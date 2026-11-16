# Decisions and Proposals

This log separates handover-confirmed direction from recommendations that still need approval. No architecture proposal below changes a confirmed requirement.

## Confirmed by the Validata handover

- Validata is a greenfield Python desktop application; the legacy Bulk Media Validator is read-only reference material.
- Validator and Counter are equally important primary capabilities.
- Discovery and validation should progress concurrently, dispatch through FIFO work queues, and update the GUI only on its main thread.
- Quick, Balanced, and Thorough are the named profiles; Balanced is the proposed default. Inheritance behavior is confirmed; exact checks remain undecided.
- Ordinary operations do not modify source files. Purge is the sole permitted deletion path and is limited to genuinely Corrupted results.
- The eventual deployment target is a self-contained portable Windows executable with persistent settings/cache and no required administrator privileges.
- Target is Windows 11, 64-bit only. Windows 10 support is explicitly removed.
- Validata's own source-code license is MIT. The copyright holder/year are not established; do not invent them. The release `LICENSE` file awaits those details.
- Distribution is open source. Public repository is `https://github.com/hectordoesgorug/Validata`.
- FFmpeg/FFprobe local baseline is Gyan 9.0.2 Essentials, static, GPLv3-configured. The owner supplied hashes are verified against the current files; redistribution is not approved.
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
| PROP-010 | Build one-folder with PyInstaller first; test a one-file release build on Windows 11. Include CustomTkinter data explicitly if selected. | PyInstaller packaging is platform-specific, and CTk documents additional theme/data collection. | Proposed |
| PROP-011 | Do not redistribute the supplied FFmpeg binaries until source/notice completeness and the MIT-app/GPL-tool distribution arrangement are reviewed. | The binaries are static GPLv3 builds. Gyan publishes an FFmpeg source revision, but exact dependency sources/build materials and the legal effect of bundling still need review. | Release blocker / owner approval needed |

## Initial repository observations

The repository is on `main`, with initial commit `9e1824726c627ce3a6b74f22e7bdc975136f34bf` and current pre-Handover-1.2 commit `53640f1fa14afad7f1efa1351881a96781ac799b`. `origin` is configured as `https://github.com/hectordoesgorug/Validata.git`. At the start of this handover, tracked files were clean; `assets/icon.ico` and `assets/icon.png` were untracked, and root FFmpeg binaries were ignored. The repository contains the seven foundation docs and no implementation source. No push was made.

The legacy directory was readable for reference, but querying its Git status was denied by the environment. Its working-tree/repository state therefore remains unverified. No legacy files were modified.

## Historical Handover 1.1 audit (superseded by the current baseline below)

- Handover 1.1 inspected a previous FFmpeg 8.0 pair. The owner replaced those binaries before Handover 1.2; that earlier audit is superseded and is not the current dependency baseline.
- `assets/icon.png` is a readable/visually inspected 1024×1024 PNG. `assets/icon.ico` has six bounded icon images (16–256 px) and opened successfully in the Windows icon decoder. Both are appropriate in roles documented in Architecture; both remain unchanged and uncommitted.
- Historic architecture and requirements docs then targeted Windows 10/11 and are corrected in Handover 1.2.
- `.gitignore` excludes root-level FFmpeg executables and generated stress fixtures. It does not ignore `assets/` or documentation. Icons remain untracked user assets.

## Handover 1.2 dependency audit

- Both current executables report `9.0.2-essentials_build-www.gyan.dev`, GCC 16.2.0, matching configuration, and the same FFmpeg library versions. Both are valid x64 PE files (`0x8664`).
- `certutil -hashfile` matches the owner-supplied SHA-256 values: `ffmpeg.exe` = `3256173f3f8bffd7df12227c68adf68025edb1832273a9530688a7bb1ed8edec`; `ffprobe.exe` = `f0d36ecbbdd3bcfac3efa078c96c7271c2e68b3810595552ac3b7f17e9a65c52`. These are local file fingerprints, not publisher-verified archive hashes.
- Build flags include `--enable-gpl --enable-version3 --enable-static`, with no `--enable-nonfree`. Gyan classifies its 64-bit static builds as GPLv3. Exact flags, source references, distribution considerations, and compliance gaps are in [Third-party notices](THIRD_PARTY_NOTICES.md).
- The icon files are unchanged and readable, but remain untracked. Asset ownership/provenance is not established.
- Windows 11 x64 is now the sole target. CustomTkinter, minimum Python version, storage fallback, validation methods, formats, Counter grammar, Purge identity, exemptions, project copyright details, and FFmpeg redistribution strategy remain owner decisions as listed below.

## Decisions still open

See [Requirements: Open questions](REQUIREMENTS.md#open-questions). Owner decisions are grouped below; none should be inferred from the technical recommendations in this record.

### Owner decisions required

**Licensing and release:** supply MIT copyright holder/year; choose FFmpeg redistribution strategy; approve third-party notice/source organization; establish icon ownership/provenance.

**Platform and tooling:** select minimum supported Python version; approve or reject CustomTkinter; approve portable-data fallback and migration behavior.

**Validation:** approve first-release format coverage and authoritative file-type policy; approve methods for Quick/Balanced/Thorough; set timeout and environmental-error classification rules; define profile schema versioning/migration.

**Counter:** approve sequence grammar/grouping, inference confidence/ambiguity behavior, and default recursion/extension policies.

**Filesystem safety:** approve symlink/junction behavior, exact Purge identity checks, and exemption storage/invalidation.

**Release management:** define versioning/release process and dependency update/verification policy.
