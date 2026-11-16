# Roadmap

This is a proposed sequence of work, not an approved feature schedule. Release dates and scope are open.

## Stage 0 — Foundation (current)

- Record owner-approved requirements, architecture boundaries, and implementation details still requiring technical work.
- Keep the approved target at Windows 11 x64/Python 3.13 x64 with the approved Tkinter GUI stack and user-managed optional FFmpeg/FFprobe.

## Stage 1 — Technical spikes and decisions

- Establish technically meaningful v1.0.0 extension coverage and evidence-based per-format checks across all five approved categories.
- Benchmark Quick/Balanced/Thorough methods, configurable timeouts, decoding/reading limits, and truthful result classifications.
- Prototype bounded task/event queues, publish-discovery-before-enqueue ordering, cancellation, completion accounting, and responsiveness using synthetic datasets.
- Verify portable read/write probing, `%LOCALAPPDATA%\Validata\` fallback, visible active path, settings/cache persistence, and atomic cache writes.
- Validate file-identity/Purge behavior, cancellation of external processes, and symlink/junction traversal policies on Windows 11.
- Specify Counter inference confidence, sequence grammar, and ambiguity UX using representative examples.
- Verify configured FFmpeg/FFprobe path/version compatibility and exercise independent checks when either tool is unavailable.
- Verify CustomTkinter, `ttk.Treeview`, standard Tk dialogs, main-thread-only updates, and packaging on Windows 11.
- Define representative real-file/stress corpora and the owner-approved release test checklist.

## Stage 2 — Application foundation

- Create the approved package structure, domain result models, settings/cache schema, logging, and job lifecycle.
- Add focused unit and integration test fixtures; do not commit generated stress datasets.
- Add the approved GUI shell and main-thread event bridge.
- Keep per-file results in transient job state for v1; no permanent history/database.

## Stage 3 — Validator capability

- Implement only approved format adapters and profile behavior.
- Verify classification quality against representative real files and controlled malformed/corrupted cases.
- Add safety-gated Purge and exemption flows after their identity rules are approved.

## Stage 4 — Counter capability

- Implement candidate pattern inference with confidence and manual sequence rules.
- Report gaps, duplicates, inconsistent names, unexpected files, and count discrepancies separately.
- Validate against an approved corpus of normal and ambiguous naming patterns.

## Stage 5 — Hardening and portable release

- Exercise 1k, 10k, and 50k workloads; nested trees; mixed formats; cancellation; network/permission failures; long paths; GUI responsiveness; and memory use.
- Test portable storage for writable/read-only directories, moved copies, and multiple copies.
- Test PyInstaller one-folder packaging, writable-data behavior, then the candidate one-file release build.
- Complete dependency inventory, external-tool documentation, version metadata, SHA-256 artifact checksums, and release documentation.
- Verify no FFmpeg/FFprobe binaries are included in Git, PyInstaller bundles, portable ZIPs, or GitHub Releases.
- Publish only after all checks pass and the owner explicitly approves the SemVer tag and GitHub Release.

No Validator or Counter implementation is included in the current foundation assignment.

## Next milestone

Recommend **Handover 2.0 — Application Foundation** as the next milestone. Its scope should implement the approved package shell, GUI/event bridge, job coordinator, settings/cache/logging, and tests. Validator and Counter capabilities should follow the technical spikes and retain the approved read-only and safety boundaries.
