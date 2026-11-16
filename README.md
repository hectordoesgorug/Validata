# Validata

Validata is a new Python desktop application planned around two equally important capabilities: file validation and sequence/consistency checking. This repository currently contains the project foundation and technical proposals; Validator and Counter are not implemented.

## Project status

The confirmed product direction, workflow, safety requirements, and open decisions are recorded in [Requirements](docs/REQUIREMENTS.md). The proposed architecture and technical trade-offs are in [Architecture](docs/ARCHITECTURE.md). See [Decisions](docs/DECISIONS.md) for the distinction between confirmed decisions and proposals, and [Roadmap](docs/ROADMAP.md) for staged work.

## Development

The implementation language is Python 3.13, 64-bit. The approved GUI stack is CustomTkinter for the primary interface, `ttk.Treeview` for results tables, and standard Tkinter utilities for native dialogs and supporting functionality. No application functionality is implemented yet.

The target is Windows 11, 64-bit only. Windows 10 is not a Validata target.

## Portable data

Portable mode stores `settings.json`, `cache.json`, and `validata.log` beside the executable when writable. Otherwise it uses `%LOCALAPPDATA%\Validata\`. Settings must show the active storage path. See [Architecture](docs/ARCHITECTURE.md#portable-data-location).

FFmpeg and FFprobe are user-managed optional dependencies: Validata will not download, bundle, or redistribute them in v1.0.0. Users can configure their independently obtained executable locations. Without these tools, validation methods that do not require them remain available; see [Third-party notices](docs/THIRD_PARTY_NOTICES.md).

## Legacy reference

Bulk Media Validator is reference material only. Validata is greenfield: no legacy source, configuration, test data, or packaging files are part of this repository.

## License

Validata source code is licensed under the [MIT License](LICENSE), copyright (c) 2026 hectordoesgorug. Third-party components have separate terms. Validata does not bundle or redistribute FFmpeg/FFprobe; users obtain those tools independently. Any future redistribution requires a separate licensing and compliance review.
