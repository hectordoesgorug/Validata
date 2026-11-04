# Architecture Proposal

**Status: proposal for review.** This is a maintainable starting point derived from the handover and legacy assessment, not a final architecture approval.

## Proposed source layout

```text
src/validata/
├── app.py                 # composition root and application lifecycle
├── presentation/          # GUI views, dialogs, and main-thread presenters
├── application/           # use cases, job orchestration, and result policies
├── discovery/             # iterative filesystem traversal and file records
├── validation/            # dispatcher, profiles, result types, adapters
│   └── adapters/           # image, video, audio, archive, document strategies
├── counter/               # pattern inference, manual rules, consistency analysis
├── jobs/                  # cancellation, bounded work queues, worker lifecycle
├── persistence/           # settings and cache interfaces/implementations
├── logging_config.py
└── resources/             # only app-owned resources, never legacy assets
tests/
├── unit/
├── integration/
└── performance/
```

Keep the GUI as a thin presentation layer. It submits commands and renders immutable job events/results; it should not own validation rules or filesystem traversal. Application services coordinate discovery, validation, Counter, persistence, and cleanup. Domain types (file snapshot, validation profile, validation result, sequence rule, Counter finding) should not depend on Tkinter or a particular persistence library.

## GUI framework

CustomTkinter is the stated preference under consideration. It preserves a Tkinter-style event loop and can suit a compact desktop utility, but it should be compared with standard Tkinter/ttk for theme, accessibility, packaging, maintainability, and testing needs before approval. Avoid adding a second UI framework or async framework without a demonstrated need. Keep presentation behind small interfaces so the application layer remains testable without a live window.

## Concurrency and event flow

Use one job coordinator with a producer for iterative discovery, a bounded FIFO queue of file snapshots, and a fixed worker pool. The producer inserts a discovery event for each accepted file and enqueues a validation task as capacity permits. Workers consume tasks, call a format adapter, and publish immutable result events to a thread-safe event queue. A main-thread UI poll drains events in bounded batches and inserts/updates individual Treeview rows.

The bounded task queue applies backpressure: when it fills, discovery pauses until workers consume tasks, while UI events continue to be drained. Use a distinct event channel or otherwise ensure UI progress/results cannot be starved behind work submissions. FIFO guarantees dequeue order only. Results can complete out of order; attach stable file/job IDs and update the corresponding row.

At end of discovery, signal producer completion. Finish only after the producer is done and every accepted item has a terminal result or explicit cancellation/error state. Perform one completion cleanup pass on the UI thread to remove only Valid results. Leave Corrupted and all nonstandard/error/skipped results for review, as directed by the handover. Cancellation stops traversal and queue intake, marks undispatched work as not started/cancelled, and allows active adapters to finish or time out cooperatively. Completed results remain visible. Never call widget methods from worker threads; never block the UI while joining workers.

For very large jobs, avoid retaining redundant full-path/task/result copies. Store compact file/job records keyed by stable IDs, expose bounded in-flight work, and measure Treeview scale and memory at 10k/50k. Progress should distinguish discovered, queued, running, completed, and not started rather than suggest one simple FIFO completion percentage.

## Validation engine and adapters

The dispatcher selects an adapter from detected category/format and passes an explicit profile plus a captured file snapshot and cancellation/time budget. Adapters return a structured result, not a boolean. The result should include classification, applied profile, method/evidence summary, timestamps, and error details safe for display/logging. Adapter code must not mutate the source.

An adapter reports **Unsupported** when no suitable check exists, **Validation Error** for tool/runtime/I/O failure, **Encrypted / Protected** when protection prevents the check, and **Incomplete / Partially readable** only when an adapter has evidence that some content is readable while integrity/completeness remains uncertain. Do not map timeouts, missing tools, access denial, or unsupported codecs to Corrupted. Profile definitions should be data-driven and versioned, but each method still needs format-specific justification and empirical evaluation.

For video, separate metadata/container inspection from packet/frame decoding. Quick may use bounded metadata/probe checks; Balanced and Thorough can increase decode coverage if performance and accuracy testing justify it. Exact mode content is an open question. Use controlled subprocess arguments, timeouts, bounded output, and reliable child-process cleanup. Treat FFprobe success as evidence of parseable metadata/streams, not proof that all media payload decodes.

## Purge boundary

Only the application service responsible for Purge should have source-file deletion capability. UI code sends an explicit confirmed Purge command containing eligible corrupted-result IDs. Before deletion, re-read identity metadata and compare with the validation snapshot; if changed or unavailable, skip and ask for revalidation. Consider an optional digest for high assurance, recognizing its cost. Exemptions must be tied to a stable content digest and must not silently make a non-corrupt result eligible for deletion.

## Counter engine

Counter is independent from validation. Its input is a folder snapshot and either inferred sequence candidates or a user-defined rule. Pattern inference proposes candidate groups (shared stem, digit position/width, extension, directory scope) with confidence and examples; it should not silently choose among ambiguous patterns. Manual rules define grouping, number extraction, expected start/step, allowed extensions, treatment of gaps/duplicates/unmatched files, and recursion scope.

Analysis returns structured findings: missing numbers/ranges, duplicate numbers, inconsistent names, unexpected/unmatched files, and counts. Distinguish a count mismatch from proven missing sequence values. Keep detection deterministic and testable with tables of examples; no source files are modified.

## Persistence, logging, external tools

Define narrow settings/cache interfaces and version their serialized schemas. Prefer an explicit per-user data directory by default, with portable-mode placement and fallback behavior to be decided. Never assume the executable directory is writable. Cache entries need invalidation keys that include enough file identity and validation-method/profile version to avoid reusing stale results. Logs should be useful for diagnosis without unnecessary personal path exposure; define retention and redaction policy before release.

Resolve FFmpeg/FFprobe paths through a small tool manager that supports bundled and unavailable states. Keep external binaries outside Python code imports and invoke them with safe argument lists, explicit timeouts, and resource limits. Packaging owns the chosen binaries, notices, and source/compliance artifacts.

## Proposed directory growth

Add code, tests, CI, and packaging configuration only after architecture and unresolved product choices are approved. A Python package under `src/` is proposed to reduce accidental imports from the repository root. No legacy source or assets should be brought into this tree.
