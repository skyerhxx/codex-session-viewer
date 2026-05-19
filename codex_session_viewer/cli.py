from __future__ import annotations

import argparse
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence

from .parser import DEFAULT_SESSIONS_DIR, load_sessions
from .renderer import render_html


DEFAULT_OUTPUT = Path("codex-sessions.html")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.command == "build":
        return build_command(args)
    if args.command == "serve":
        return serve_command(args)
    parser.print_help()
    return 2


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-session-viewer",
        description="Render ~/.codex/sessions JSONL history as a browser viewer.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Generate a standalone HTML report.")
    build.add_argument(
        "--sessions-dir",
        default=str(DEFAULT_SESSIONS_DIR),
        help="Directory containing Codex session JSONL files. Default: ~/.codex/sessions",
    )
    build.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="HTML file to write. Default: codex-sessions.html",
    )
    build.add_argument("--title", default="Codex Sessions", help="HTML page title.")

    serve = subparsers.add_parser("serve", help="Serve the viewer on localhost and rebuild on refresh.")
    serve.add_argument(
        "--sessions-dir",
        default=str(DEFAULT_SESSIONS_DIR),
        help="Directory containing Codex session JSONL files. Default: ~/.codex/sessions",
    )
    serve.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    serve.add_argument("--port", type=int, default=12001, help="Port to listen on. Default: 12001")
    serve.add_argument("--title", default="Codex Sessions", help="HTML page title.")
    serve.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    return parser


def build_command(args: argparse.Namespace) -> int:
    sessions_dir = Path(args.sessions_dir).expanduser()
    output = Path(args.output).expanduser()
    sessions = load_sessions(sessions_dir)
    html = render_html(sessions, title=args.title)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Wrote {output} with {len(sessions)} sessions from {sessions_dir}")
    return 0


def serve_command(args: argparse.Namespace) -> int:
    sessions_dir = Path(args.sessions_dir).expanduser()
    title = args.title

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in {"/", "/index.html"}:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")
                return
            sessions = load_sessions(sessions_dir)
            html = render_html(sessions, title=title).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Serving Codex sessions from {sessions_dir}")
    print(f"Open {url}")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
