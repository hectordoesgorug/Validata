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

## Profiles and result classifications — proposed, subject to technical approval

Three profiles are proposed: **Quick**, **Balanced**, and **Thorough**. Balanced is the proposed default. Users should be able to set a global default and category overrides for Video, Audio, Images, Archives, and Documents. Each result records the applied profile.

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

## Safety — confirmed

Ordinary discovery, validation, and Counter operations never modify originals. Deletion is permitted only through the explicitly authorized Purge operation. Preserve confirmation dialogues, individual and bulk Purge, SHA-256-based exemptions, and exempt/de-exempt operations. Investigate verifying file identity or content again immediately before Purge so files changed since validation are not deleted based on stale results.

## Jobs and filesystem — confirmed goals; details open

Preserve button blocking where it protects job consistency. Investigate graceful cancellation, stopping discovery, preventing queued files from starting, dealing safely with active workers, retaining completed results, and identifying unfinished work. Resumable jobs are not required for initial release unless investigation finds a compelling reason.

Handle permission errors, files disappearing or changing during work, symlinks and junctions, long paths and names, and network interruptions. Avoid expensive filesystem operations unless they are needed for correctness or safety.

## Deployment — confirmed target

The eventual target is a portable Windows executable with no mandatory installation or administrator rights, plus predictable persistent settings and cache handling. A one-folder development build followed by a one-file release build is acceptable. FFmpeg licensing and redistribution compliance must be resolved for the exact binaries and configuration selected.

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
4. What settings/cache location should be used for portable mode, including read-only folders, removable media, and multiple app copies?
5. Which FFmpeg build is acceptable, and who will maintain its source offer, notices, build configuration, and license review?
6. What minimum Windows version and Python runtime are release targets?
7. What sequence grammars, extensions, recursion rules, and grouping rules should Counter detect automatically? How should ambiguous detections be surfaced for manual setup?
8. Should symlinks and junctions be followed, ignored, or handled through an explicit option?
9. Which identity snapshot (for example path, size, timestamps, file ID, and/or digest) is sufficient to guard Purge without excessive overhead?
10. What project license, versioning scheme, and release process should be adopted?
