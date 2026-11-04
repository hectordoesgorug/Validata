# Validata

Validata is a new Python desktop application planned around two equally important capabilities: file validation and sequence/consistency checking. This repository currently contains the project foundation and technical proposals; Validator and Counter are not implemented.

## Project status

The confirmed product direction, workflow, safety requirements, and open decisions are recorded in [Requirements](docs/REQUIREMENTS.md). The proposed architecture and technical trade-offs are in [Architecture](docs/ARCHITECTURE.md). See [Decisions](docs/DECISIONS.md) for the distinction between confirmed decisions and proposals, and [Roadmap](docs/ROADMAP.md) for staged work.

## Development

The implementation language is Python. CustomTkinter is the preferred GUI framework under consideration, not yet an approved dependency. Exact runtime and development dependencies will be selected after architecture approval. No dependency installation is required to review these planning documents.

## Legacy reference

Bulk Media Validator is reference material only. Validata is greenfield: no legacy source, configuration, test data, or packaging files are part of this repository.

## License

Project licensing has not yet been decided. FFmpeg redistribution also requires a build-specific license and notices review before release.
