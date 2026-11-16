# Roadmap

This is a proposed sequence of work, not an approved feature schedule. Release dates and scope are open.

## Stage 0 — Foundation (current)

- Record confirmed requirements, architecture proposals, open questions, and technical recommendations.
- Review the local repository setup and approve the architecture and unresolved choices with the product/planning owner.

## Stage 1 — Technical spikes and decisions

- Confirm minimum Python version for the Windows 11 x64 target; complete CustomTkinter evaluation with ttk Treeview and packaging behavior.
- Define first-release supported formats and evidence-based profile checks.
- Prototype bounded task/event queues, publish-discovery-before-enqueue ordering, cancellation, completion accounting, and responsiveness using synthetic datasets.
- Approve portable data fallback, copy isolation, visibility/migration behavior; validate file identity strategies for safe Purge.
- Obtain owner approval for FFmpeg redistribution strategy; verify matching Corresponding Source and dependency notices or evaluate another build.
- Specify Counter detection and manual configuration behavior with representative naming examples.
- Approve staged first-release format coverage; validate profile inheritance and method definitions.
- Obtain the MIT copyright holder/year and establish icon asset provenance before creating complete license/attribution materials.

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
- Complete dependency inventory, FFmpeg license/notice/source handling, version metadata, and release documentation.

No Validator or Counter implementation is included in the current foundation assignment.

## Proposed next milestone

Recommend **Handover 2.0 — Application Foundation** only after the owner has reviewed and approved the remaining architecture choices that affect the shell, job lifecycle, storage, and release dependency model. That handover should authorize a narrowly scoped foundation (package shell, GUI/event bridge, job coordinator, settings/cache/logging, and tests) while continuing to defer Validator and Counter behavior until separately approved.
