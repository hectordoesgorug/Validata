# Architecture Proposal

**Status: architecture direction established; implementation details remain proposals unless marked confirmed in Requirements or Decisions.** No application implementation is authorized by this handover.

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

**Approved GUI stack:** CustomTkinter for the primary GUI, `ttk.Treeview` for results tables, and standard Tkinter utilities for native dialogs/supporting functionality. Keep GUI presentation separate from Validator and Counter logic. All widget operations belong to the main thread; workers communicate through thread-safe queues/events. Keep discovery, validation, and cancellation responsive. Do not add another GUI or async framework without approval. Keep presentation behind small interfaces so application logic can be tested without a live window.

Retain a color-coded Treeview and include textual result labels so color is not the sole status signal.

## Concurrency and event flow

Use one job coordinator with a producer for iterative discovery, a bounded FIFO task queue, a fixed worker pool, and a separate bounded event queue shared by producer/workers and polled by the UI thread. For each file, the scanner must: (1) discover it, (2) assign a stable job/file ID and capture a lightweight identity snapshot, (3) publish a compact `FileDiscovered` event, and only then (4) enqueue its validation task. Thus a full validation queue can pause further discovery only after the just-discovered file's row has been published. The UI can insert that row while the scanner waits for task capacity.

The bounded task queue applies backpressure when workers lag. The bounded event queue applies backpressure if the GUI falls behind; it must not become an unbounded second backlog. Queue capacities should be fixed/configurable limits measured against compact event payloads. The main thread drains events on a short scheduled tick in bounded batches and never waits on queue puts or worker joins. If a worker is blocked publishing a result because the event queue is full, the UI remains able to drain it. Use a separate small/coalesced mechanism for replaceable progress counters so progress noise cannot crowd out discovery/results. Queue ownership is explicit: the coordinator owns task admission and job counts; scanner is the only task producer; workers are task consumers and event producers; UI is the only event consumer and the only owner of Treeview mutation.

The single event queue preserves enqueue order. Since the scanner publishes `FileDiscovered` before admitting the corresponding task, a worker cannot publish that file's result before its discovery event has entered the event queue. FIFO guarantees task dequeue/dispatch order, not completion order; multiple workers can finish out of order, so results target rows by stable IDs. UI handling must tolerate cancellation/closing and stale job IDs.

At end of discovery, publish a producer-done event after all its discovery events and task admissions. The coordinator emits `JobCompleted` only after discovery is done, all accepted tasks have a terminal or explicitly not-started state, and each worker has published its final event. Because all event producers use the same FIFO event queue, the UI receives all prior row/result events before `JobCompleted`; it can then perform cleanup safely. Track accepted, queued, running, terminal, and cancelled/not-started counts under coordinator ownership. On failure, publish compact job/file error events; workers catch and report exceptions instead of silently losing tasks. Cancellation sets a shared signal, stops traversal, makes queue puts interruptible (timed puts that check cancellation), and ensures queued tasks are drained/marked not started rather than accidentally executed. Workers check cancellation before invoking adapters; active adapters use cooperative checks/timeouts and are joined off the UI thread. Completed results remain visible. Perform one completion cleanup pass on the UI thread to remove only Valid results. Leave Corrupted and all nonstandard/error/skipped results for review. Never call widget methods from worker threads or block the UI while joining workers.

For very large jobs, avoid retaining redundant full-path/task/result copies. Store compact file/job records keyed by stable IDs, expose bounded in-flight work, and measure Treeview scale and memory at 10k/50k. Progress should distinguish discovered, queued, running, completed, and not started rather than suggest one simple FIFO completion percentage.

Do not show percentage completion until discovery has established a total file count. Cancellation must stop discovery and prevent queued tasks from starting; active adapters may finish or stop at safe checkpoints/timeouts. The coordinator must mark unfinished accepted tasks explicitly and preserve results already completed. Resumable jobs are not required for v1.

## Validation engine and adapters

The dispatcher selects an adapter from detected category/format and passes an explicit profile plus a captured file snapshot and cancellation/time budget. Adapters return a structured result, not a boolean. The result should include classification, applied profile, method/evidence summary, timestamps, and error details safe for display/logging. Adapter code must not mutate the source.

An adapter reports **Unsupported** when no suitable check exists, **Validation Error** for tool/runtime/I/O failure, **Encrypted / Protected** when protection prevents the check, and **Incomplete / Partially readable** only when an adapter has evidence that some content is readable while integrity/completeness remains uncertain. Do not map timeouts, missing tools, access denial, or unsupported codecs to Corrupted. Profile definitions should be data-driven and versioned, but each method still needs format-specific justification and empirical evaluation.

Select adapters first from filename extension, then verify content using signatures, headers, container metadata, or structure where supported. Report extension/content mismatches. Detect extensionless supported files through signatures where feasible; unknown extensions alone are not Corrupted. Avoid full-file reads solely for identification. Quick uses fast structural/metadata checks with minimal reads; Balanced performs deeper structural/readability checks without routinely decoding entire large media files; Thorough uses the deepest supported checks and may fully decode media or verify archive integrity. Exact algorithms, thresholds, and resource limits require implementation-phase testing. Label sampled checks as sampled. Use controlled subprocess arguments, configurable timeouts, bounded output, safe cancellation/termination, and reliable child-process cleanup. FFprobe metadata success does not prove full payload decoding. Missing FFmpeg/FFprobe must produce an explicit non-corruption result when a required check cannot run, never an unearned Valid result.

## Purge boundary

Only the dedicated Purge service should have source-file deletion capability. Individual and bulk Purge are separate confirmed actions and require explicit confirmation. Bulk Purge accepts only confidently Corrupted, non-exempt results; all other classifications are ineligible. Record the validated path, size, modification time, and available filesystem identity; recheck immediately before deletion. Skip changed, missing, or unverifiable files and require revalidation. Never follow symlinks or junctions to delete their targets. Avoid unnecessary SHA-256 recomputation. SHA-256 exemptions persist in `cache.json`, apply to identical content across locations/names, and must not remain valid after content changes. Cache reuse requires consistent file identity metadata; writes must be atomic. Exemption storage is distinct from temporary validation-result cache data. Exact Windows identity handling and safe deletion API need implementation testing.

## Counter engine

Counter is independent from validation. Its input is a folder snapshot and either inferred sequence candidates or a user-defined rule. Pattern inference proposes candidate groups (shared stem, digit position/width, extension, directory scope) with confidence and examples; it should not silently choose among ambiguous patterns. Manual rules define grouping, number extraction, expected start/step, allowed extensions, treatment of gaps/duplicates/unmatched files, and recursion scope.

Analysis returns structured findings: missing numbers/ranges, duplicate numbers, inconsistent names, unexpected/unmatched files, and counts. Distinguish a count mismatch from proven missing sequence values. Keep detection deterministic and testable with tables of examples; no source files are modified.

## Persistence, logging, external tools

### Portable data location

**Approved portable layout:** `Validata.exe`, `settings.json`, `cache.json`, and `validata.log` in the executable directory when writable. Probe write access without risking existing data. If unavailable, use `%LOCALAPPDATA%\Validata\`; show the active path in Settings. Preserve settings/cache across updates and avoid silently distributing files across unrelated paths. Atomic persistence, recovery, and update handling are implementation-phase details. No per-copy fallback, migration, or path-hashing behavior is approved.

Define narrow settings/cache interfaces and version their serialized schemas. A small JSON settings file and compact cache are sufficient initially; detailed persistent validation history is out of scope, so no database is proposed. Cache entries need invalidation keys that include enough file identity and validation-method/profile version to avoid reusing stale results. Logs should be useful for diagnosis without unnecessary personal path exposure; define retention and redaction policy before release. The active storage location must be visible in the UI and included in diagnostic context.

**Approved dependency model:** FFmpeg/FFprobe are optional, user-managed external tools. Do not download, install, bundle, or redistribute them in v1.0.0. Provide the [Gyan download page](https://www.gyan.dev/ffmpeg/builds/), let users select the folder containing both executables, verify availability/version/compatibility, and persist configured paths. If either tool is missing at validation start, explain the missing executable and affected methods, explain that independent checks remain available, and offer Continue, Cancel, and Configure FFmpeg/FFprobe. Continue with independent methods; do not silently classify affected files Valid or Corrupted solely due to a missing tool. Keep executables outside Python imports and launch via safe argument lists, configured timeouts, bounded output, and reliable cancellation. Future redistribution requires separate owner and licensing review.

### Validation profile resolution

Persist a configurable global default of **Balanced** and optional overrides for `Video`, `Audio`, `Images`, `Archives`, and `Documents`. A category without an override inherits the global setting; changing the global value preserves explicit overrides; each category can reset to inherit. Resolve when creating a task and store the effective profile, profile-definition version, and method in its result. Quick means fast structural/metadata checks with minimal reads; Balanced means deeper readability checks without routine full large-media decoding; Thorough means deepest supported checks, potentially including full media decoding and archive integrity reads. Exact algorithms, thresholds, and profile schema migration remain implementation decisions. Never represent sampled work as complete integrity verification.

### Working results and history

The Treeview/job model is transient working state, not permanent detailed history. Keep discovered rows throughout the active job, update row status/color incrementally, and remove Valid rows in one cleanup after all work finishes. Preserve problematic/nonstandard rows and aggregate statistics for the completed in-memory job. On application exit, per-file job results need not persist. No database or permanent record of removed Valid files is required for the initial release. Future export or history features require separate approval.

### Filesystem traversal

Do not recursively follow directory symlinks or junctions in Validator or Counter. Detect loops and avoid duplicate paths through linked directories or overlapping selected roots. File symlinks may be validated through accessible targets; broken/inaccessible links produce non-corruption errors. Ordinary validation never modifies targets; Purge never follows links to delete targets. Report inaccessible directories, permission failures, changing/disappearing files, long paths, and network interruptions. Counter recursively scans folders, grouping immediate files per folder by default and considering all regular-file extensions unless filtered. Keep Windows-specific identity and path behavior in infrastructure adapters. How Counter represents file-symlink entries and exact Purge treatment without following a target need implementation design.

## v1.0.0 format scope

Legacy extension inventory reviewed: JPEG/PNG/GIF/BMP/TIFF/WebP plus SVG/ICO/RAW/HEIC family; common video/audio containers and codecs; PDF and multiple text/office/book formats; ZIP/RAR/7z/TAR/gzip/bzip2/xz. The current legacy code itself performs materially different levels of checking, so the extension inventory is not an accuracy baseline.

Recommended staged candidates (subject to approval and representative tests):

| Group | First-release candidates | Evidence/limits |
| --- | --- | --- |
| Images | JPEG, PNG, GIF, BMP, TIFF, WebP | Decode with a maintained image library; report decoder/readability evidence, not semantic correctness. HEIC support adds a codec plug-in dependency. |
| Archives/containers | ZIP, EPUB, TAR, gzip, bzip2, xz | Full member/stream reads can surface CRC/truncation errors. EPUB adds required-package structure checks; ZIP central directory alone is insufficient. |
| Documents | PDF, TXT, CSV, XML; DOCX/ODT as ZIP containers | Parser or syntax checks only. CSV is not schema validation; XML is well-formedness only; PDF encryption/protection can block checks; office container checks do not validate application semantics. |
| Audio/video | A curated set of common FFmpeg-probe-supported extensions after tool audit | External tool required. Probe is metadata/stream inspection; stronger profiles may decode bounded packets/content after accuracy, time, and resource tests. |
| Defer pending dedicated support | SVG as renderable image, ICO, RAW camera types, DOC/PPT legacy binaries, RAR, 7z, MOBI, KPUB, PEZ | Basic byte reads are not meaningful integrity checks. Select only with suitable maintained parser/decoder and clear Unsupported behavior. |

The five categories (Images, Videos, Audio, Documents, Archives) are confirmed for v1.0.0. This does not approve every extension in the legacy inventory. Each extension must have a meaningful method and explicit evidence limits. Exact lists, algorithms, and claims remain implementation decisions requiring representative fixtures.

## Platform and packaging assessment

Confirmed target: **Windows 11 x64 with Python 3.13 x64**; Windows 10 and other operating systems are not targets. PyInstaller builds must run on Windows and be tested on Windows 11. The approved GUI stack is CustomTkinter with `ttk.Treeview` and standard Tkinter dialog utilities. Keep validation/Counter domain logic independent from Tkinter and isolate Windows filesystem behavior behind adapters. References: [Python Windows support](https://docs.python.org/3/using/windows.html), [PyInstaller manual](https://pyinstaller.org/en/stable/), [CustomTkinter packaging](https://customtkinter.tomschimansky.com/documentation/packaging/).

## Supplied binary and icon audit status

The current FFmpeg/FFprobe baseline and exact flags, hashes, source references, and licensing notes are centralized in [Third-party notices](THIRD_PARTY_NOTICES.md). The tools report common media demuxers and decoders, including H.264, HEVC, AV1, VP9, MPEG-2/4, ProRes, AAC, MP3, Opus, FLAC, Vorbis, and WMA. This makes them technically suitable candidates for media probe/decode validation; actual accuracy, resource use, CPU compatibility, and behavior with representative files still require evaluation. An FFprobe stream listing is not proof that all payload decodes.

The matching embedded version/configuration and library versions indicate companion binaries from the same build family, but the owner-provided fingerprints are not publisher-verified provenance. The supplied binaries remain local ignored development files and must not be staged. The approved v1.0.0 policy is not to distribute them; any future proposal requires separate owner and licensing review.

The owner confirms `assets/icon.png` and `assets/icon.ico` were generated using ChatGPT and approves their use as Validata branding. The PNG opens as 1024×1024; the ICO opens with Windows icon decoding. Both are tracked and remain unchanged. Record only this provenance and approval; do not claim independently verified originality or copyright protection.

## Proposed directory growth

Add code, tests, CI, and packaging configuration only after architecture and unresolved product choices are approved. A Python package under `src/` is proposed to reduce accidental imports from the repository root. No legacy source or assets should be brought into this tree.
