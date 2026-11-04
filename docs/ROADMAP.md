# Roadmap

This is a proposed sequence of work, not an approved feature schedule. Release dates and scope are open.

## Stage 0 — Foundation (current)

- Record confirmed requirements, architecture proposals, open questions, and technical recommendations.
- Review the local repository setup and approve the architecture and unresolved choices with the product/planning owner.

## Stage 1 — Technical spikes and decisions

- Compare CustomTkinter with Tkinter/ttk for the required Treeview, accessibility, and packaging behavior.
- Define first-release supported formats and evidence-based profile checks.
- Prototype bounded discovery/worker/result flow and UI responsiveness using synthetic datasets.
- Validate file identity strategies for safe Purge and define settings/cache locations.
- Select and audit the FFmpeg/FFprobe distribution and licensing path.
- Specify Counter detection and manual configuration behavior with representative naming examples.

## Stage 2 — Application foundation

- Create the approved package structure, domain result models, settings/cache schema, logging, and job lifecycle.
- Add focused unit and integration test fixtures; do not commit generated stress datasets.
- Add the approved GUI shell and main-thread event bridge.

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
- Test PyInstaller one-folder packaging, writable-data behavior, then the candidate one-file release build.
- Complete dependency inventory, FFmpeg license/notice/source handling, version metadata, and release documentation.

No Validator or Counter implementation is included in the current foundation assignment.
