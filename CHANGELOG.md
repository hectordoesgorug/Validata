# Changelog

All notable changes to Validata are recorded here.

## Unreleased

- Add Validator file/folder source selection, streaming recursive discovery, duplicate suppression for overlapping paths, and progressive result rows.
- Add a bounded FIFO task queue, two-worker default pool, job IDs and lifecycle accounting, cooperative cancellation, and close-after-cancel behavior. Infrastructure tasks report **Not Validated**; no file contents are read and integrity validation remains unavailable.
- Skip directory symlinks and junctions; accept accessible file symlinks and report broken links as discovery errors. Document bounded event backpressure and filesystem-call cancellation limits.
- Add deterministic discovery/job tests and a synthetic 1,000-file tree workload; see Architecture for environment and measured result.
- Implement the Python 3.13 package foundation, CustomTkinter shell with Validator/Counter workspaces, shared ttk results tables, Settings, portable storage resolver, atomic JSON settings, rotating logging, and bounded main-thread event pump.
- Add foundational pytest coverage and PowerShell development setup/launch documentation.
- Keep all file processing unavailable; no Validator or Counter behavior is simulated.
- Consolidate Handover 1.3 owner decisions across platform, GUI, portable storage, user-managed FFmpeg/FFprobe, traversal, Purge, file detection, profiles, Counter, exemptions, and releases.
- Add the MIT `LICENSE` and document the approved ChatGPT-generated application icon provenance.
- Record Python 3.13 x64, CustomTkinter/ttk, and user-managed optional FFmpeg/FFprobe policies.
- Record the prior Handover 1.2 Windows 11/MIT baseline and FFmpeg 9.0.2 audit; Handover 1.3 supersedes its distribution-policy status.
- Add a dedicated third-party notices and licensing record.
- Establish initial project documentation and technical proposals from the approved handover.
- No validation, Counter processing, discovery, Purge, exemption, FFmpeg integration, or job scheduler features implemented.
