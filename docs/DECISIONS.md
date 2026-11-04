# Decisions and Proposals

This log separates handover-confirmed direction from recommendations that still need approval. No architecture proposal below changes a confirmed requirement.

## Confirmed by the Validata handover

- Validata is a greenfield Python desktop application; the legacy Bulk Media Validator is read-only reference material.
- Validator and Counter are equally important primary capabilities.
- Discovery and validation should progress concurrently, dispatch through FIFO work queues, and update the GUI only on its main thread.
- Quick, Balanced, and Thorough profiles are proposed; Balanced is the proposed default. Exact checks remain undecided.
- Ordinary operations do not modify source files. Purge is the sole permitted deletion path and is limited to genuinely Corrupted results.
- The eventual deployment target is a self-contained portable Windows executable with persistent settings/cache and no required administrator privileges.
- Do not implement Validator or Counter during the foundation assignment; do not push the initial documentation without review and approval.

## Technical recommendations — approval needed

| ID | Recommendation | Rationale | Status |
| --- | --- | --- | --- |
| PROP-001 | Organize implementation as a `src/validata` package with separate presentation, application, discovery, validation adapters, Counter, jobs, and persistence modules. | Enforces boundaries and allows domain logic to be tested without the GUI. | Proposed |
| PROP-002 | Use one producer, a bounded FIFO task queue, a fixed worker pool, and a thread-safe result/event channel polled by the UI thread. | Matches the progressive workflow while adding backpressure and thread-safe UI updates. | Proposed |
| PROP-003 | Model outcomes as structured classifications with evidence and profile metadata; never conflate environmental/tool failures with corruption. | Prevents false positive deletion and supports inspection of nonstandard results. | Proposed |
| PROP-004 | Make Counter infer candidates with confidence and require manual rules for ambiguous patterns. | Avoids silently treating unrelated names or files as one sequence. | Proposed |
| PROP-005 | Revalidate captured file identity before Purge and skip changed/unavailable files. | Reduces stale-result deletion risk. | Proposed |
| PROP-006 | Keep CustomTkinter under evaluation against Tkinter/ttk before choosing the UI dependency. | Framework preference is known; trade-offs and packaging fit remain unassessed. | Proposed |
| PROP-007 | Build a one-folder PyInstaller development artifact first and a one-file release artifact only after runtime-data and FFmpeg handling are validated. | Easier diagnosis during development; one-file mode extracts bundled resources at runtime and needs careful path/licensing handling. | Proposed |
| PROP-008 | Store persistent state in a deliberate writable data location, not implicitly beside the executable. | Portable folders may be read-only or on removable/network media. Exact portable-mode policy remains open. | Proposed |

## Initial repository observations

At assignment start, the Validata directory contained zero entries and had no Git repository metadata. Consequently there was no existing branch, history, or configured remote to inspect. The intended remote URL is recorded in the handover, but network retrieval of that GitHub page was unavailable during this inspection; remote ownership/content could not be independently verified. This documentation commit initializes local history only and does not push.

The legacy directory was readable for reference, but querying its Git status was denied by the environment. Its working-tree/repository state therefore remains unverified. No legacy files were modified.

## Decisions still open

See [Requirements: Open questions](REQUIREMENTS.md#open-questions). In particular, profile checks, initial format coverage, sequence grammar, data-directory behavior, minimum Windows target, project license, and FFmpeg build/compliance need decisions before corresponding implementation or release work.
