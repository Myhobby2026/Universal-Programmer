# Universal Programmer Studio

Universal Programmer Studio is a Windows 10/11 desktop application for operating a Teensy 4.1 USB controller and explicitly validated target-device adapters. It is deliberately capability-gated: a profile is not treated as programmable merely because it uses SPI, I²C, JTAG, SWD, or UART.

## Current implementation

The repository contains a working hardware-independent foundation and a Qt
desktop shell:

- PySide6 IDE-style window with dark, light, and system theme choices.
- Dockable explorer, target information, terminal, operation log, and progress panels.
- Eighteen named workspaces for dashboard, file/memory work, device catalog,
  interface workspaces, analyzer, terminal, history, and settings.
- Persistent JSON settings, Qt window state, and named workspace snapshots.
- SQLite persistence for recent files and operation history.
- A CRC-16 framed USB serial protocol, incremental parser, real serial owner,
  and deterministic mock transport for tests.
- Real binary and Intel HEX parsing, checksums, editable memory buffers with
  undo/redo, capture CSV export, and serialized operation state handling.
- Explicit profile metadata for a small, honest initial catalog. Hardware
  operations are disabled until a compatible firmware capability and validated
  target profile are present.
- Teensy 4.1 Arduino firmware implementing versioned protocol discovery and
  safe capability reporting. Target-specific programming algorithms remain
  gated until an adapter and algorithm are added.
- Hardware-independent pytest coverage and a Windows PyInstaller build script.

The application shell is intentionally honest about unfinished hardware
algorithms: interface tabs are present for workflow organization, but they do
not claim target detection or programming success.

## Quick start

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.main
```

The GUI can be inspected without a Teensy. It will display **Not connected** and will not fabricate detection or programming results. To run tests:

```powershell
python -m pytest -q
```

## Build a Windows executable

```powershell
.\scripts\build.ps1
```

This invokes PyInstaller only; it does not flash firmware or imply hardware validation. See `docs/INSTALLATION.md`, `docs/USER_GUIDE.md`, and `docs/HARDWARE.md`.

## Repository layout

```text
app/                 Application entry point
core/                Models, settings, themes, operation engine
transport/           Framed protocol and serial transport
devices/             SQLite catalog and device profiles
file_formats/        Binary and Intel HEX parsers
memory/              Editable memory buffer
programmers/         Capability-gated programmer service contracts
analyzer/             Capture data model and CSV export
ui/                  Main window, tabs, docks, dialogs
firmware/             Teensy 4.1 Arduino firmware and protocol notes
storage/              SQLite persistence
tests/               Hardware-independent tests
docs/                Installation, user, hardware, protocol, troubleshooting
scripts/              Windows install/build helpers
```

## Hardware status

No physical Teensy, target IC, level shifter, adapter, or target-specific flash algorithm is assumed to be present. The application reports the actual USB connection state and exposes only operations supported by both firmware capabilities and the selected profile. See `docs/SUPPORTED_DEVICES.md` for the initial catalog and limitations.
