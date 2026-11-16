# Decisions and Proposals

This log separates owner-approved project decisions from implementation details that still require technical design, testing, or benchmarking.

## Confirmed owner decisions

- Validata is a greenfield Python desktop app with two primary capabilities: Validator and Counter. Do not migrate or copy the legacy Bulk Media Validator.
- Supported platform: Windows 11 x64 only, using Python 3.13 x64. No Windows 10 or other-OS compatibility commitment.
- GUI: CustomTkinter primary interface, `ttk.Treeview` results tables, and standard Tkinter utilities for native dialogs/supporting functions. All widget operations run on the main thread; workers communicate through thread-safe queues/events.
- Portable target: no mandatory installation or administrator rights. Store `settings.json`, `cache.json`, and `validata.log` beside the executable when writable; otherwise use `%LOCALAPPDATA%\Validata\`. Show the active location and preserve settings/cache across updates.
- FFmpeg/FFprobe are optional user-managed dependencies. Validata v1.0.0 will not automatically download/install, bundle, or redistribute them. Users select the folder containing the executables; configured paths persist and availability/version/compatibility are checked. Missing tools cannot alone produce Corrupted or a silent Valid result when a required method was skipped. Independent methods remain usable. The supplied 9.0.2 Gyan pair is development-only and ignored by Git.
- User-facing dependency guidance links to https://www.gyan.dev/ffmpeg/builds/. Future distribution requires separate owner approval and licensing/compliance review.
- Application source is MIT-licensed; root `LICENSE` carries `Copyright (c) 2026 hectordoesgorug`. Third-party tools retain their own licensing.
- `assets/icon.png` and `assets/icon.ico` are ChatGPT-generated and approved for Validata branding. Do not claim independently verified originality or copyright protection.
- Directory symlinks and junctions are not recursively followed in Validator or Counter. Accessible file symlinks may be validated through their targets. Ordinary operations do not modify originals; Purge must not follow links to delete targets.
- File detection starts with extension-based adapter selection and verifies content through signatures/headers/metadata where supported. Mismatches are explicit; unknown extensions alone are not corruption; extensionless signature recognition is supported where feasible.
- v1.0.0 retains Images, Videos, Audio, Documents, and Archives, without automatically approving the legacy extension list.
- Profiles are Quick, Balanced, and Thorough; global default Balanced; category overrides inherit/reset as documented in Requirements. Results record effective profile and method. Partial checks are not represented as complete integrity checks.
- Counter recursively scans selected folders, groups immediate files per folder by default, considers all regular-file extensions unless filtered, infers patterns, and presents ambiguity for user choice. It is read-only; count mismatches alone do not prove missing sequence values.
- Purge requires explicit confirmation and immediate identity recheck. Changed, missing, or unverifiable files are skipped and require revalidation. Bulk Purge applies only to confidently Corrupted, non-exempt results.
- SHA-256 exemptions persist in `cache.json`, apply to identical content, are invalidated when content changes, and are excluded from bulk Purge. Cache writes are atomic and exemptions remain separate from temporary validation-result caching.
- Validation results are session-only; keep rows through the active job, remove Valid rows after full completion, preserve problematic results and aggregate counts. No permanent detailed history/database in v1.0.0.
- Discovery publishes each file row before waiting on bounded FIFO validation queue admission. Main-thread UI updates, separate bounded queues, explicit job/cancellation states, and responsive cancellation remain required.
- Releases use Semantic Versioning: `0.x.x` during development and `1.0.0` for the first stable release. Maintain `CHANGELOG.md`; use versioned tags; publish through GitHub Releases with SHA-256 checksums and dependency versions. Testing and explicit owner approval gate release.
- Handover 2.0 authorizes only the application foundation scope; Validator/Counter processing and other excluded features remain out of scope. Codex must not commit, push, tag, or publish without owner approval.

## Implementation details still requiring technical work

| Area | Remaining design/verification |
| --- | --- |
| Validation | Supported extensions, adapter algorithms, thresholds, sampling/decode depth, accurate evidence and classifications. |
| Timeouts | Exact per-adapter/profile values, cancellation checkpoints, and external-process termination tests. |
| File identity/Purge | Windows filesystem identity availability, race-resistant deletion implementation, and safe treatment of file-symlink entries. |
| Profiles/cache | Schema versioning, migration, atomic-write recovery, and validation-result cache invalidation details. |
| FFmpeg | Compatible version range, paired-tool checks, path selection UX, and independent validation coverage. |
| Counter | Sequence grammar, confidence scoring, examples, and ambiguity presentation. |
| GUI/packaging | Accessibility review, Windows 11 behavior, packaging and main-thread/event-bridge verification. |
| Testing/release | Representative real-file corpus, stress workloads, release test checklist, checksums, and approval workflow. |

## Historical Handover 1.2 audit

Handover 1.2 recorded the supplied FFmpeg 9.0.2 Essentials binaries as static, GPLv3-configured builds. Local hashes matched owner-provided fingerprints but were not publisher-verified. Under Handover 1.3, the binaries are development-only; user-managed dependency policy replaces earlier packaging/distribution proposals. See [Third-party notices](THIRD_PARTY_NOTICES.md) for audit details and licensing limits.

The previous handover left the icons untracked, but commit `a9bdb09` subsequently added both approved assets. They are now tracked and unchanged.

## Handover 2.0 foundation

The implemented initial package, GUI shell, portable storage resolver, settings, logging, and event pump are described in [Architecture](ARCHITECTURE.md). The Settings schema is version 1 and contains appearance mode and window geometry only; `cache.json` remains reserved. No validation, Counter, discovery, FFmpeg integration, Purge, or job scheduler behavior is implemented.
