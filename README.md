# Validata

Validata is a Python desktop application planned around two equally important capabilities: file validation and sequence/consistency checking. The application shell and workspace structures are implemented; Validator and Counter processing are not.

## Project status

The confirmed product direction and safety requirements are in [Requirements](docs/REQUIREMENTS.md). Current foundation architecture and remaining technical work are in [Architecture](docs/ARCHITECTURE.md) and [Decisions](docs/DECISIONS.md); staged work is in [Roadmap](docs/ROADMAP.md).

## Development

The target is Python 3.13 x64 on Windows 11 x64. The GUI uses CustomTkinter for the primary interface, `ttk.Treeview` for results tables, and standard Tkinter utilities for native dialogs. The foundation currently includes Validator and Counter workspaces, shared tables, Settings, portable storage resolution, JSON settings, rotating logs, and a bounded main-thread event pump.

### Development setup (PowerShell)

Install Python 3.13 x64, then from the repository root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m validata
```

Run the automated tests with:

```powershell
python -m pytest
```

`pyproject.toml` defines bounded dependencies (`customtkinter>=6,<7`, `pytest>=8,<10`). The foundation was verified with Python 3.13.17, CustomTkinter 6.0.0, and pytest 9.2.0.

## Portable data

In a packaged portable build, storage is beside the executable when writable; otherwise it uses `%LOCALAPPDATA%\Validata\`. During development it uses the ignored project-local `.validata-data/` directory, falling back to LocalAppData if needed. Settings displays the active directory. Settings are stored in `settings.json`; `cache.json` is reserved for future caching/exemptions; logs use `validata.log`.

The approved future FFmpeg/FFprobe model is user-managed and optional: Validata will not download, bundle, or redistribute them in v1.0.0. External-tool setup and validation integration are not implemented yet. See [Third-party notices](docs/THIRD_PARTY_NOTICES.md).

The current GUI is structural only. File/folder selection, validation, Counter analysis, and other processing controls are unavailable; no results are simulated.

## Legacy reference

Bulk Media Validator is reference material only. Validata is greenfield: no legacy source, configuration, test data, or packaging files are part of this repository.

## License

Validata source code is licensed under the [MIT License](LICENSE), copyright (c) 2026 hectordoesgorug. Third-party components have separate terms. Validata does not bundle or redistribute FFmpeg/FFprobe; users obtain those tools independently. Any future redistribution requires a separate licensing and compliance review.
