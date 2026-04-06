# Conlang Studio Desktop GUI

Electron + React + Material UI wrapper for the Python conlang engine.

## Features

- Quick language generation from any template (including pseudo real-world profiles)
- Full manual builder with section-level skipping
- Translation, generation, daughter-language derivation, style switching
- Translation deconstruction with per-token dictionary lookup
- Pronounceability evaluation panel
- Custom frameless topbar with window controls
- Ultra-thin custom scrollbar (2px, transparent track, no buttons)
- Multi-theme flat visual system

## Run

From repository root:

- `bootstrap_and_run_gui.bat`

Manual run:

1. Install Python requirements: `python -m pip install -r requirements.txt`
2. Change into GUI folder: `cd gui`
3. Install GUI dependencies: `npm.cmd install`
4. Start GUI: `npm.cmd run dev`

## Build Frontend Bundle

- From `gui` folder: `npm.cmd run build`

## Build Desktop EXE

From repository root:

- Build both CLI and desktop: `build_exe.bat all`
- Build CLI only: `build_exe.bat cli`
- Build desktop only: `build_exe.bat desktop`

Manual desktop packaging (from `gui` folder):

1. Install dependencies: `npm.cmd install`
2. Build frontend + package unpacked desktop app: `npm.cmd run build:desktop`
3. Optional installer build: `npm.cmd run build:desktop:installer`

Desktop artifacts are written to `dist/desktop` in the repository root.

Note: desktop packages run the Python bridge. Ensure Python is installed on target machines, or set `CONLANG_STUDIO_PYTHON` to a specific Python executable path.

## Architecture

- `gui/electron` Electron main + preload
- `gui/src` React UI
- `src/gui_bridge.py` Python bridge used by Electron IPC
