# Validata

Validata is a new Python desktop application planned around two equally important capabilities: file validation and sequence/consistency checking. This repository currently contains the project foundation and technical proposals; Validator and Counter are not implemented.

## Project status

The confirmed product direction, workflow, safety requirements, and open decisions are recorded in [Requirements](docs/REQUIREMENTS.md). The proposed architecture and technical trade-offs are in [Architecture](docs/ARCHITECTURE.md). See [Decisions](docs/DECISIONS.md) for the distinction between confirmed decisions and proposals, and [Roadmap](docs/ROADMAP.md) for staged work.

## Development

The implementation language is Python. CustomTkinter is the preferred GUI framework, pending final technical evaluation. No application functionality is implemented yet.

The target is Windows 11, 64-bit only. Windows 10 is not a Validata target.

## Portable data

The intended portable mode stores settings, cache, and logs beside the executable when that directory is writable. If it is not, the proposal is to use a predictable per-user fallback and tell the user which location is active. See the storage proposal in [Architecture](docs/ARCHITECTURE.md#portable-data-location). The exact fallback behavior remains subject to review.

## Legacy reference

Bulk Media Validator is reference material only. Validata is greenfield: no legacy source, configuration, test data, or packaging files are part of this repository.

## License

Validata's source-code license is MIT. The copyright holder and year still need to be supplied before a complete `LICENSE` file can be added; no name has been inferred. Third-party components have separate terms. The supplied FFmpeg/FFprobe binaries are GPLv3-configured; see [Third-party notices](docs/THIRD_PARTY_NOTICES.md). Their redistribution strategy has not been approved.
