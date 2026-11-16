# Requirements

Status labels distinguish confirmed owner decisions from technical implementation details that still require design, testing, or benchmarking.

## Product capabilities — confirmed

Validata has two equally important primary capabilities:

- **Validator:** detect corruption and assess integrity across supported formats; use format-specific strategies and configurable profiles; retain problematic and nonstandard results for inspection.
- **Counter:** evolve file-count comparison into a sequence and consistency checker. Initially detect sequence and naming patterns automatically, permit manual configuration when detection is ambiguous, and report missing sequence numbers, duplicate numbering, naming inconsistencies, unexpected files, and relevant count discrepancies.

## Validator workflow — confirmed

1. The user selects files or directories.
2. Discovery proceeds progressively. Each found file appears in the Treeview and becomes eligible for validation immediately.
3. Files are dispatched to validation workers through a FIFO queue. Multiple workers may run concurrently, so result completion order is not guaranteed to match dispatch order.
4. Per-row result updates and all other GUI operations run on the main UI thread. Workers communicate through thread-safe queues; updates should be batched where useful without rebuilding the whole Treeview.
5. Discovery and validation continue concurrently. Bounded queues provide backpressure and constrain in-flight work.
6. All discovered files remain visible for the active job. At job completion, valid files are removed in a cleanup operation; problematic and nonstandard results remain visible.

Before blocking on a full validation task queue, the scanner must publish that file's discovery event to the GUI-event path so the row can appear. Bound the task and event queues independently; event traffic must not be starved by task backpressure. Exact capacities and batch sizes are implementation choices to benchmark.

Track at least Discovered, Queued, Running, Completed, and Not started / cancelled states. Do not show percentage completion until discovery establishes the total. A job completes only when discovery has ended and every accepted task has a terminal result or explicit cancellation/error state. Cancellation stops discovery, prevents queued work from starting, lets active adapters finish or stop at safe checkpoints/timeouts, preserves completed results, and identifies unfinished work. Worker joins must not block the GUI.

## Profiles and result classifications

The named profiles are **Quick**, **Balanced**, and **Thorough**; the global default is **Balanced**. Users may set category overrides for Video, Audio, Images, Archives, and Documents. Each result records the effective profile and method. Exact per-format algorithms remain implementation decisions requiring technical evaluation and benchmarking.

Quick performs fast structural and metadata checks with minimal file reading. Balanced performs more comprehensive structural/readability checks without routinely decoding entire large media files. Thorough performs the deepest supported validation and may fully decode media or verify complete archive integrity. Methods and thresholds are not defined. FFmpeg/FFprobe are optional user-managed dependencies for relevant audio/video checks.

The result vocabulary is:

- Valid
- Corrupted
- Incomplete / Partially readable
- Unsupported
- Encrypted / Protected
- Validation Error
- Skipped

Format-specific rules must explain the evidence behind a result and distinguish an actual integrity failure from an inability to check. Only results confidently classified as **Corrupted** may be eligible for bulk Purge.

Sampled checks must be described as sampled; never present them as complete integrity verification. Full video decoding is not assumed for Balanced. Timeouts and environmental failures never establish corruption. Missing tools must not silently produce Valid results where required methods did not run.

### Profile inheritance — confirmed configuration behavior; methods remain open

The global default profile is configurable. A category without an explicit override inherits it. Changing the global default preserves every explicit category override; each category can separately be reset to inherit. Each result records the effective profile used. Profile definitions are versioned so future changes can be identified. Exact per-format checks and thresholds remain open; no guarantee of complete decode or detection is implied.

## Results and history — confirmed initial scope

Every discovered file remains in the working Treeview while a job is active; row status and color update as outcomes arrive. Keep the familiar color-coded presentation but include a textual status so color is never the only signal. Valid rows are removed only after the whole job has completed. Problematic and nonstandard outcomes remain available for inspection, and aggregate counts for every result category remain available after completion. Persistent detailed per-file validation history is outside initial-release scope. Do not add a database or permanent valid-file records just to preserve the job list. Exportable reports or detailed history may be considered separately later.

## Safety — confirmed

Ordinary discovery, validation, and Counter operations never modify originals. Deletion is permitted only through the explicitly authorized Purge operation. Individual and bulk Purge require explicit confirmation. Before deletion, recheck path, size, modification time, and available filesystem identity; skip files that changed, disappeared, or cannot be verified and require revalidation. Purge must not follow symlinks or junctions to delete their targets. Avoid unnecessary SHA-256 recalculation.

Only confidently classified Corrupted results can be eligible for bulk Purge. Exempted files are excluded. Unsupported, Encrypted / Protected, Incomplete / Partially readable, Validation Error, and Skipped results are not bulk-purge eligible. No repair, rename, move, compression, or other source-file modification is permitted. Users can review, add, and remove SHA-256 exemptions. Exemptions persist in `cache.json`, apply to identical content across names/locations, and must be invalidated when content changes. Cache reuse is allowed only while file identity metadata remains consistent; update cache files atomically. Exemption storage remains logically distinct from temporary validation-result caching.

## Jobs and filesystem — confirmed goals; details open

Preserve button blocking where it protects job consistency. Investigate graceful cancellation, stopping discovery, preventing queued files from starting, dealing safely with active workers, retaining completed results, and identifying unfinished work. Resumable jobs are not required for initial release unless investigation finds a compelling reason.

Do not recursively follow directory symlinks or junctions in Validator or Counter. Detect traversal loops; do not duplicate paths through linked directories or overlapping selected roots. File symlinks may be validated through accessible targets; broken or inaccessible links receive a non-corruption error. Ordinary operations never modify link targets, and Purge never follows links to delete targets. Report inaccessible directories, permission failures, disappearing/changing files, long paths, and network interruptions explicitly rather than silently suppressing them. Counter recursively inspects selected folders, treating each folder's immediate files as a separate group by default.

## Deployment — confirmed target

The eventual target is a portable Windows executable with no mandatory installation or administrator rights. A one-folder development build followed by a one-file release build is acceptable. FFmpeg/FFprobe are user-managed optional dependencies and will not be bundled or redistributed in v1.0.0.

The supported platform is **Windows 11 64-bit only**, using **Python 3.13 64-bit**. Windows 10 and other operating systems are out of scope.

Portable mode places `settings.json`, `cache.json`, and `validata.log` beside the executable when writable, falling back to `%LOCALAPPDATA%\Validata\`. Settings must display the active location. Preserve settings and cache across application updates. Avoid silently scattering data among unrelated locations. Atomic persistence, recovery, and update handling are implementation-phase details; see [Architecture](ARCHITECTURE.md#portable-data-location).

## GUI — confirmed

Use CustomTkinter for the primary GUI, `ttk.Treeview` for results tables, and standard Tkinter utilities for native dialogs and supporting functionality. Widget operations run only on the main thread; workers communicate through thread-safe events/queues. Keep the GUI responsive during discovery, validation, and cancellation. Text labels must accompany status colors. Do not introduce another GUI or async framework without approval.

## File-type detection — confirmed policy

First use the filename extension to select an initial adapter. Where supported, verify content with signatures, headers, container metadata, or structural information. Report extension/content mismatches explicitly. Recognize extensionless files by signatures where feasible. Unknown extensions alone are not corruption. Avoid unnecessary full-file reads and never rename or modify source files.

## First-release categories — confirmed

Retain Images, Videos, Audio, Documents, and Archives as the five v1.0.0 categories. Do not treat the legacy extension inventory as approved coverage. Each supported extension needs a technically meaningful method; document reliable structural checks, partial readability checks, comprehensive checks, and unsupported/deferred formats separately. Exact extension lists and algorithms remain for subsequent technical work.

## Counter defaults — confirmed

Recursively inspect selected folders and subfolders without following directory symlinks/junctions. By default, each folder's immediate regular files form a separate sequence group, and all regular files are considered regardless of extension unless filtered. Infer numbering patterns automatically, present ambiguous candidates for user selection, and support manual pattern, start, increment, and grouping rules. Report gaps, duplicates, naming inconsistencies, and count discrepancies separately; a count mismatch alone does not prove missing numbers. Counter remains read-only.

## Timeouts and external tools — confirmed policy

Timeouts are configurable by adapter and profile: Quick shorter, Balanced moderate, Thorough longer. Exact values require testing and benchmarking. Timeouts never automatically establish corruption. Distinguish missing dependencies, permission failures, interrupted reads, and unavailable storage from corruption. Terminate external FFmpeg processes safely when cancellation or timeout requires it, and record why a check could not complete.

Users select the folder containing both `ffmpeg.exe` and `ffprobe.exe`. Verify availability, version, and compatibility, and persist the configured locations. When either tool is missing at validation start, warn which executable is unavailable, explain which audio/video methods need it and that independent methods remain available. Offer **Continue**, **Cancel**, and **Configure FFmpeg/FFprobe**. A missing executable cannot alone yield Corrupted, and files for which required methods did not run must not silently be called Valid. Record the non-corruption reason. Continue must permit checks that do not need the missing tools.

## Performance and quality targets — confirmed test coverage

The proposed test strategy must cover workloads of 1,000, 10,000, and 50,000 files; nested directories; mixed formats; malformed and corrupted inputs; concurrent discovery and validation; cancellation; responsiveness; memory use; Purge safety; and Counter sequence detection. Synthetic stress data should be generated outside permanent application data and not committed. Representative real files are needed to evaluate actual accuracy and media decoding performance.

## Constraints — confirmed

- Greenfield implementation; do not migrate, fork, or copy the legacy application.
- Do not implement Validator or Counter as part of the foundation assignment.
- Do not install unnecessary dependencies or add unnecessary frameworks.
- Do not assume validation accuracy without evidence.
- Do not change confirmed requirements without raising the change for review.

## Open questions

1. Which formats and exact extensions have a sufficiently meaningful v1.0.0 validation method?
2. What exact per-format algorithms, thresholds, sampling/decode depth, and resource limits define each profile?
3. What configurable timeout values and non-corruption classifications apply per adapter?
4. What versioned profile/cache schema migration and recovery behavior is required?
5. What filesystem identity fields are available and required on supported Windows 11 filesystems for safe Purge?
6. How should file-symlink entries themselves be represented in Counter and handled by Purge without following targets?
7. What sequence grammar and confidence scoring should automatic Counter inference use?
8. Which external-tool version range is compatible, and how should configured executable paths and paired tools be checked?
9. What accessibility, packaging, and Windows 11 verification is required for the approved GUI stack?
10. Which representative real-file and stress-test corpora are approved for accuracy and performance evaluation?
11. What release testing and owner-approval checklist will gate tags and GitHub Releases?

## Versioning and releases — confirmed

Use Semantic Versioning: `0.x.x` during initial development and `1.0.0` for the first stable public release. Patch releases carry backward-compatible fixes, minor releases backward-compatible features, and major releases breaking compatibility changes. Maintain `CHANGELOG.md`; use versioned Git tags such as `v1.0.0`; publish artifacts through GitHub Releases with SHA-256 checksums and dependency versions documented. Require testing and explicit owner approval before publication.

## Counter — confirmed scope, open grammar

Counter is independent from Validator and never modifies source files. It must report missing sequence numbers/ranges, duplicate numbering, inconsistent names, unexpected/unmatched files, and count discrepancies; a count mismatch alone is not proof of a missing number. Automatic pattern inference proposes candidate groups with confidence and examples and must not silently select an ambiguous pattern. Manual rules cover grouping, extraction, expected start/step, extensions, gaps, duplicates, unmatched files, and recursion scope. Exact grammar, confidence threshold, and default recursion behavior remain open.

## Initial format coverage — recommendation for approval

The legacy application lists 17 image, 14 video, 10 audio, 14 document, and 7 archive extensions. This is a reference inventory, not a promise that all should ship initially. Recommended first-release candidates, subject to approval and actual fixture testing:

- **Best candidates for meaningful structural checks:** PNG, JPEG, GIF, BMP, TIFF, and WebP images using a maintained decoder; ZIP/EPUB and OOXML containers where central-directory/member CRC checks are meaningful; TAR and gzip/bzip2/xz streams with full-read integrity checks; XML well-formedness. These checks establish structural/readability evidence, not semantic correctness or perfect recovery.
- **Basic readability or syntax only:** TXT (encoding/read failures), CSV (parser/read checks, not schema correctness), and PDF (parser/page/object checks, subject to encryption and parser limitations). Clearly describe what was and was not examined.
- **External-tool candidates:** common video/container and audio families through a selected FFmpeg/FFprobe build. Probe-only results are metadata/stream checks; selected profiles may decode bounded packets or content. Exact extensions and checks depend on the executable audit and benchmarks.
- **Limited or uncertain; defer from initial automatic support unless dedicated tooling is approved:** proprietary camera RAW variants; SVG as an image (XML parsing is not renderer/security validation); old binary Office formats (`.doc`, `.ppt`); RAR and 7z; MOBI; and legacy/specialized `.kpub` and `.pez`. Basic header readability alone must not be reported as integrity validation.

The product expectation remains multi-format, format-specific validation across Video, Audio, Images, Archives, and Documents. This staged list recommends first-release scope; approval is needed before any formats are excluded or any format is advertised as validated. See [Architecture: format coverage](ARCHITECTURE.md#v100-format-scope).
