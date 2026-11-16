# Requirements

Status labels distinguish confirmed handover requirements from proposals and unresolved questions. “Confirmed” means supplied in the Validata handover; it does not imply that implementation details are settled.

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

The named profiles are **Quick**, **Balanced**, and **Thorough**; Balanced is the proposed default. Users should be able to set a global default and category overrides for Video, Audio, Images, Archives, and Documents. Each result records the applied profile. The inheritance behavior below is confirmed; exact profile methods and the result vocabulary remain proposals subject to technical approval.

Methods and thresholds are not defined. Full video decoding may be expensive and is not assumed for every profile. FFmpeg and FFprobe are expected to be important for audio/video checks.

The proposed result vocabulary is:

- Valid
- Corrupted
- Incomplete / Partially readable
- Unsupported
- Encrypted / Protected
- Validation Error
- Skipped

Format-specific rules must explain the evidence behind a result and distinguish an actual integrity failure from an inability to check. Only results confidently classified as **Corrupted** may be eligible for bulk Purge.

Sampled checks must be described as sampled; never present them as complete integrity verification. Full video decoding is not assumed for Balanced because it may be prohibitively expensive across the owner's hundreds of movie files.

### Profile inheritance — confirmed configuration behavior; methods remain open

The global default profile is configurable. A category without an explicit override inherits it. Changing the global default preserves every explicit category override; each category can separately be reset to inherit. Each result records the effective profile used. Profile definitions are versioned so future changes can be identified. Exact per-format checks and thresholds remain open; no guarantee of complete decode or detection is implied.

## Results and history — confirmed initial scope

Every discovered file remains in the working Treeview while a job is active; row status and color update as outcomes arrive. Keep the familiar color-coded presentation but include a textual status so color is never the only signal. Valid rows are removed only after the whole job has completed. Problematic and nonstandard outcomes remain available for inspection, and aggregate counts for every result category remain available after completion. Persistent detailed per-file validation history is outside initial-release scope. Do not add a database or permanent valid-file records just to preserve the job list. Exportable reports or detailed history may be considered separately later.

## Safety — confirmed

Ordinary discovery, validation, and Counter operations never modify originals. Deletion is permitted only through the explicitly authorized Purge operation. Preserve confirmation dialogues, individual and bulk Purge, SHA-256-based exemptions, and exempt/de-exempt operations. Investigate verifying file identity or content again immediately before Purge so files changed since validation are not deleted based on stale results.

Only Corrupted results can be eligible for bulk Purge. Unsupported, Encrypted / Protected, Incomplete / Partially readable, Validation Error, and Skipped results are not bulk-purge eligible. No repair, rename, move, compression, or other source-file modification is permitted. Identical content should share exemption status; exemption persistence and invalidation remain open.

## Jobs and filesystem — confirmed goals; details open

Preserve button blocking where it protects job consistency. Investigate graceful cancellation, stopping discovery, preventing queued files from starting, dealing safely with active workers, retaining completed results, and identifying unfinished work. Resumable jobs are not required for initial release unless investigation finds a compelling reason.

Handle permission errors, files disappearing or changing during work, symlinks and junctions, long paths and names, and network interruptions. Do not silently suppress errors. Avoid expensive filesystem operations unless they are needed for correctness or safety. Not following directory symlinks/junctions recursively by default remains a recommendation, not an approved decision.

## Deployment — confirmed target

The eventual target is a portable Windows executable with no mandatory installation or administrator rights, plus predictable persistent settings and cache handling. A one-folder development build followed by a one-file release build is acceptable. FFmpeg licensing and redistribution compliance must be resolved for the exact binaries and configuration selected.

The initial OS target is **Windows 11 64-bit only**. Windows 10 is explicitly out of scope; do not document Windows 10 as a Validata compatibility target.

Portable mode should place settings, cache, and logs beside the executable when writable. The application must not assume that directory is writable. A deterministic fallback, visible active-location indicator, update persistence, and behavior for multiple copies are required. The recommended fallback is documented as a proposal in [Architecture](ARCHITECTURE.md#portable-data-location).

## Performance and quality targets — confirmed test coverage

The proposed test strategy must cover workloads of 1,000, 10,000, and 50,000 files; nested directories; mixed formats; malformed and corrupted inputs; concurrent discovery and validation; cancellation; responsiveness; memory use; Purge safety; and Counter sequence detection. Synthetic stress data should be generated outside permanent application data and not committed. Representative real files are needed to evaluate actual accuracy and media decoding performance.

## Constraints — confirmed

- Greenfield implementation; do not migrate, fork, or copy the legacy application.
- Do not implement Validator or Counter as part of the foundation assignment.
- Do not install unnecessary dependencies or add unnecessary frameworks.
- Do not assume validation accuracy without evidence.
- Do not change confirmed requirements without raising the change for review.

## Open questions

1. Which formats are in the first release, and what file-type/extension/content-detection policy is authoritative?
2. What exact Quick, Balanced, and Thorough methods and thresholds apply per format, including decode depth and time/resource limits? How are profile-definition changes migrated?
3. How should timeout and environmental failures be classified while keeping them ineligible for Purge?
4. Should the proposed `%LOCALAPPDATA%\Validata\PortableFallback\<copy-id>` fallback and migration behavior be approved?
5. Which minimum 64-bit CPython version should be pinned for Windows 11 and the selected UI/package dependencies?
6. Should CustomTkinter receive final approval after evaluating theme, accessibility, Windows 11 behavior, Treeview integration, packaging, maintainability, and testability?
7. Which sequence grammar, grouping, extensions, and recursion rules should Counter use? What confidence threshold and ambiguity flow should be used?
8. Should recursive discovery follow symlinks/junctions? The current recommendation is no by default, but this is not approved.
9. Which path/size/time/file-ID checks should Purge require, and when is digest re-verification justified?
10. How should SHA-256 exemptions be stored, invalidated, and de-exempted?
11. What versioning and release process should be adopted?
12. Is the GPLv3 FFmpeg distribution strategy acceptable for an MIT project? What source/notice package and delivery channels will be maintained?
13. Who is the MIT copyright holder, and what year should appear in `LICENSE`?
14. Who owns or created the supplied icon artwork, and what attribution/license applies?

## Counter — confirmed scope, open grammar

Counter is independent from Validator and never modifies source files. It must report missing sequence numbers/ranges, duplicate numbering, inconsistent names, unexpected/unmatched files, and count discrepancies; a count mismatch alone is not proof of a missing number. Automatic pattern inference proposes candidate groups with confidence and examples and must not silently select an ambiguous pattern. Manual rules cover grouping, extraction, expected start/step, extensions, gaps, duplicates, unmatched files, and recursion scope. Exact grammar, confidence threshold, and default recursion behavior remain open.

## Initial format coverage — recommendation for approval

The legacy application lists 17 image, 14 video, 10 audio, 14 document, and 7 archive extensions. This is a reference inventory, not a promise that all should ship initially. Recommended first-release candidates, subject to approval and actual fixture testing:

- **Best candidates for meaningful structural checks:** PNG, JPEG, GIF, BMP, TIFF, and WebP images using a maintained decoder; ZIP/EPUB and OOXML containers where central-directory/member CRC checks are meaningful; TAR and gzip/bzip2/xz streams with full-read integrity checks; XML well-formedness. These checks establish structural/readability evidence, not semantic correctness or perfect recovery.
- **Basic readability or syntax only:** TXT (encoding/read failures), CSV (parser/read checks, not schema correctness), and PDF (parser/page/object checks, subject to encryption and parser limitations). Clearly describe what was and was not examined.
- **External-tool candidates:** common video/container and audio families through a selected FFmpeg/FFprobe build. Probe-only results are metadata/stream checks; selected profiles may decode bounded packets or content. Exact extensions and checks depend on the executable audit and benchmarks.
- **Limited or uncertain; defer from initial automatic support unless dedicated tooling is approved:** proprietary camera RAW variants; SVG as an image (XML parsing is not renderer/security validation); old binary Office formats (`.doc`, `.ppt`); RAR and 7z; MOBI; and legacy/specialized `.kpub` and `.pez`. Basic header readability alone must not be reported as integrity validation.

The product expectation remains multi-format, format-specific validation across Video, Audio, Images, Archives, and Documents. This staged list recommends first-release scope; approval is needed before any formats are excluded or any format is advertised as validated. See [Architecture: format coverage](ARCHITECTURE.md#initial-format-coverage-proposal).
