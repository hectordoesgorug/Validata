# Roadmap

This is a proposed sequence of work, not an approved feature schedule. Release dates and scope are open.

## Stage 0 — Foundation (current)

- Record confirmed requirements, architecture proposals, open questions, and technical recommendations.
- Review the local repository setup and approve the architecture and unresolved choices with the product/planning owner.

## Stage 1 — Technical spikes and decisions

- Confirm Python version and supported Windows 10/11 policy; test a CustomTkinter shell with ttk Treeview and packaging behavior.
- Define first-release supported formats and evidence-based profile checks.
- Prototype bounded task/event queues, publish-discovery-before-enqueue ordering, cancellation, completion accounting, and responsiveness using synthetic datasets.
- Approve portable data fallback, copy isolation, visibility/migration behavior; validate file identity strategies for safe Purge.
- Resolve whether the supplied GPLv3 static FFmpeg/FFprobe build fits Validata's licensing model and arrange matching sources/notices, or evaluate another build.
- Specify Counter detection and manual configuration behavior with representative naming examples.
- Approve staged first-release format coverage; validate profile inheritance and method definitions.

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
