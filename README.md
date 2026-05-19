# Codex Session Viewer

Read Codex JSONL sessions from `~/.codex/sessions` and view them in a local HTML UI.

## Build A Standalone HTML File

```bash
python -m codex_session_viewer build --output codex-sessions.html
```

Open `codex-sessions.html` in a browser. The file is self-contained and does not need a server.

## Serve Locally

```bash
python -m codex_session_viewer serve --port 12001
```

Then open `http://127.0.0.1:12001/`. Refreshing the page rereads `~/.codex/sessions`.

## Options

```bash
python -m codex_session_viewer build --sessions-dir ~/.codex/sessions --output codex-sessions.html
python -m codex_session_viewer serve --sessions-dir ~/.codex/sessions --host 127.0.0.1 --port 12001 --no-open
```

The viewer shows session titles, working directories, timestamps, user and assistant messages, tool calls, collapsible tool outputs, and parse errors. It omits encrypted reasoning payloads and long base instruction metadata from the rendered timeline.
