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

The precise meaning of a file becoming “available” for dispatch, queue capacities, batch sizes, and cleanup timing are implementation choices to validate during development.

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

### Profile inheritance — confirmed configuration behavior; methods remain open

The global default profile is configurable. A category without an explicit override inherits it. Changing the global default preserves every explicit category override; each category can separately be reset to inherit. Each result records the effective profile used. Profile definitions are versioned so future changes can be identified. Exact per-format checks and thresholds remain open; no guarantee of complete decode or detection is implied.

## Results and history — confirmed initial scope

Every discovered file remains in the working Treeview while a job is active; row status and color update as outcomes arrive. Valid rows are removed only after the whole job has completed. Problematic and nonstandard outcomes remain available for inspection, and aggregate statistics remain available after completion. Persistent detailed per-file validation history is outside initial-release scope. Do not add a database or permanent valid-file records just to preserve the job list. Exportable reports or detailed history may be considered separately later.

## Safety — confirmed

Ordinary discovery, validation, and Counter operations never modify originals. Deletion is permitted only through the explicitly authorized Purge operation. Preserve confirmation dialogues, individual and bulk Purge, SHA-256-based exemptions, and exempt/de-exempt operations. Investigate verifying file identity or content again immediately before Purge so files changed since validation are not deleted based on stale results.

## Jobs and filesystem — confirmed goals; details open

Preserve button blocking where it protects job consistency. Investigate graceful cancellation, stopping discovery, preventing queued files from starting, dealing safely with active workers, retaining completed results, and identifying unfinished work. Resumable jobs are not required for initial release unless investigation finds a compelling reason.

Handle permission errors, files disappearing or changing during work, symlinks and junctions, long paths and names, and network interruptions. Avoid expensive filesystem operations unless they are needed for correctness or safety.

## Deployment — confirmed target

The eventual target is a portable Windows executable with no mandatory installation or administrator rights, plus predictable persistent settings and cache handling. A one-folder development build followed by a one-file release build is acceptable. FFmpeg licensing and redistribution compliance must be resolved for the exact binaries and configuration selected.

The initial OS target is **Windows 10 64-bit and Windows 11 64-bit**. The Windows 10 edition/build support policy is an open risk because standard Home/Pro Windows 10 reached end of support on October 14, 2025; distinguish still-supported LTSC/ESU cases from standard editions before publishing a support statement. [Microsoft lifecycle details](https://learn.microsoft.com/en-us/lifecycle/products/windows-10-home-and-pro).

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

1. Which formats are in the first supported release, and what is the authoritative extension/content-detection policy?
2. What exact checks and acceptance criteria define each profile by format, including video decode depth and time/resource limits?
3. How should unsupported, encrypted, incomplete, timeout, and environmental-error results map to the UI and cleanup policy?
4. Should the proposed `%LOCALAPPDATA%\Validata\PortableFallback\<copy-id>` fallback and explicit migration policy be approved?
5. What project license and FFmpeg distribution model will permit the supplied GPLv3 build, if retained?
6. Which supported 64-bit CPython version should be pinned for Windows 10/11 and the selected UI/package dependencies?
7. What sequence grammars, extensions, recursion rules, and grouping rules should Counter detect automatically? How should ambiguous detections be surfaced for manual setup?
8. Should symlinks and junctions be followed, ignored, or handled through an explicit option?
9. Which identity snapshot (for example path, size, timestamps, file ID, and/or digest) is sufficient to guard Purge without excessive overhead?
10. What versioning scheme and release process should be adopted?
11. Does “Windows 10” mean any 64-bit Windows 10 installation for application compatibility, or only still-serviced Windows 10 editions/builds for supported use?
12. Should Validata retain this GPLv3 static FFmpeg build or evaluate an LGPL-only alternative? What exact source archive, enabled-library source, build materials, notices, and source access/offer will accompany distributed executables?

## Initial format coverage — recommendation for approval

The legacy application lists 17 image, 14 video, 10 audio, 14 document, and 7 archive extensions. This is a reference inventory, not a promise that all should ship initially. Recommended first-release candidates, subject to approval and actual fixture testing:

- **Best candidates for meaningful structural checks:** PNG, JPEG, GIF, BMP, TIFF, and WebP images using a maintained decoder; ZIP/EPUB and OOXML containers where central-directory/member CRC checks are meaningful; TAR and gzip/bzip2/xz streams with full-read integrity checks; XML well-formedness. These checks establish structural/readability evidence, not semantic correctness or perfect recovery.
- **Basic readability or syntax only:** TXT (encoding/read failures), CSV (parser/read checks, not schema correctness), and PDF (parser/page/object checks, subject to encryption and parser limitations). Clearly describe what was and was not examined.
- **External-tool candidates:** common video/container and audio families through a selected FFmpeg/FFprobe build. Probe-only results are metadata/stream checks; selected profiles may decode bounded packets or content. Exact extensions and checks depend on the executable audit and benchmarks.
- **Limited or uncertain; defer from initial automatic support unless dedicated tooling is approved:** proprietary camera RAW variants; SVG as an image (XML parsing is not renderer/security validation); old binary Office formats (`.doc`, `.ppt`); RAR and 7z; MOBI; and legacy/specialized `.kpub` and `.pez`. Basic header readability alone must not be reported as integrity validation.

The product expectation remains multi-format, format-specific validation across Video, Audio, Images, Archives, and Documents. This staged list recommends first-release scope; approval is needed before any formats are excluded or any format is advertised as validated. See [Architecture: format coverage](ARCHITECTURE.md#initial-format-coverage-proposal).
