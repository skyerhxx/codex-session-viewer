from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SESSIONS_DIR = Path.home() / ".codex" / "sessions"
MAX_TEXT_CHARS = 200_000
SENSITIVE_JSON_FIELD_REPLACEMENTS = (
    (re.compile(r'("encrypted_content"\s*:\s*)"(?:\\.|[^"\\])*"', re.DOTALL), r'\1"[redacted]"'),
    (
        re.compile(r'("base_instructions"\s*:\s*\{\s*"text"\s*:\s*)"(?:\\.|[^"\\])*"', re.DOTALL),
        r'\1"[redacted]"',
    ),
    (
        re.compile(r'((?:\\)+"encrypted_content(?:\\)+"\s*:\s*(?:\\)+")(?:\\.|[^"\\])*?((?:\\)+")', re.DOTALL),
        r"\1[redacted]\2",
    ),
    (
        re.compile(
            r'((?:\\)+"base_instructions(?:\\)+"\s*:\s*\{\s*(?:\\)+"text(?:\\)+"\s*:\s*(?:\\)+")(?:\\.|[^"\\])*?((?:\\)+")',
            re.DOTALL,
        ),
        r"\1[redacted]\2",
    ),
    (re.compile(r"\bgAAAAAB[0-9A-Za-z_-]{20,}"), "[redacted encrypted blob]"),
)


def discover_session_files(sessions_dir: str | Path = DEFAULT_SESSIONS_DIR) -> list[Path]:
    root = Path(sessions_dir).expanduser()
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


def load_sessions(sessions_dir: str | Path = DEFAULT_SESSIONS_DIR) -> list[dict[str, Any]]:
    sessions = [load_session_file(path) for path in discover_session_files(sessions_dir)]
    sessions.sort(key=lambda item: item.get("updated_at") or item.get("started_at") or "", reverse=True)
    return sessions


def load_session_file(path: str | Path) -> dict[str, Any]:
    session_path = Path(path)
    meta: dict[str, Any] = {}
    events: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    seen_timestamps: list[str] = []

    with session_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                parse_errors.append(
                    {
                        "line": line_number,
                        "message": f"line {line_number}: {exc.msg}",
                        "preview": truncate_text(line, 500),
                    }
                )
                continue

            timestamp = _record_timestamp(record)
            if timestamp:
                seen_timestamps.append(timestamp)

            record_type = record.get("type")
            payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
            if record_type == "session_meta":
                meta.update(_extract_meta(payload, timestamp))
                continue

            event = _record_to_event(record_type, payload, timestamp)
            if event is not None:
                events.append(event)

    started_at = meta.get("started_at") or (min(seen_timestamps) if seen_timestamps else None)
    updated_at = max(seen_timestamps) if seen_timestamps else started_at
    session_id = meta.get("id") or _id_from_filename(session_path)

    return {
        "id": session_id,
        "path": str(session_path),
        "file_name": session_path.name,
        "cwd": meta.get("cwd") or "",
        "started_at": started_at,
        "updated_at": updated_at,
        "model_provider": meta.get("model_provider") or "",
        "cli_version": meta.get("cli_version") or "",
        "title": _session_title(events, session_path),
        "message_count": sum(1 for event in events if event.get("kind") == "message"),
        "tool_call_count": sum(1 for event in events if event.get("kind") == "tool_call"),
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "events": events,
    }


def _record_timestamp(record: dict[str, Any]) -> str | None:
    timestamp = record.get("timestamp")
    if isinstance(timestamp, str):
        return timestamp
    payload = record.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("timestamp"), str):
        return payload["timestamp"]
    return None


def _extract_meta(payload: dict[str, Any], timestamp: str | None) -> dict[str, Any]:
    return {
        "id": payload.get("id") if isinstance(payload.get("id"), str) else None,
        "started_at": payload.get("timestamp") if isinstance(payload.get("timestamp"), str) else timestamp,
        "cwd": payload.get("cwd") if isinstance(payload.get("cwd"), str) else "",
        "model_provider": payload.get("model_provider") if isinstance(payload.get("model_provider"), str) else "",
        "cli_version": payload.get("cli_version") if isinstance(payload.get("cli_version"), str) else "",
    }


def _record_to_event(record_type: str | None, payload: dict[str, Any], timestamp: str | None) -> dict[str, Any] | None:
    if record_type == "response_item":
        payload_type = payload.get("type")
        if payload_type == "message":
            return _message_event(payload, timestamp)
        if payload_type == "function_call":
            return {
                "kind": "tool_call",
                "timestamp": timestamp,
                "name": str(payload.get("name") or ""),
                "call_id": str(payload.get("call_id") or ""),
                "arguments": truncate_text(redact_sensitive_text(_stringify(payload.get("arguments"))), MAX_TEXT_CHARS),
            }
        if payload_type == "function_call_output":
            return {
                "kind": "tool_output",
                "timestamp": timestamp,
                "call_id": str(payload.get("call_id") or ""),
                "output": truncate_text(redact_sensitive_text(_stringify(payload.get("output"))), MAX_TEXT_CHARS),
            }
        return None

    if record_type == "event_msg" and payload.get("type") == "agent_message":
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            return None
        return {
            "kind": "agent_message",
            "timestamp": timestamp,
            "role": "assistant",
            "text": truncate_text(redact_sensitive_text(message), MAX_TEXT_CHARS),
        }

    return None


def _message_event(payload: dict[str, Any], timestamp: str | None) -> dict[str, Any] | None:
    role = payload.get("role")
    if role not in {"user", "assistant"}:
        return None
    text = extract_text(payload.get("content"))
    if not text.strip():
        return None
    return {
        "kind": "message",
        "timestamp": timestamp,
        "role": role,
        "text": truncate_text(redact_sensitive_text(text), MAX_TEXT_CHARS),
    }


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif "content" in item:
                    nested = extract_text(item.get("content"))
                    if nested:
                        parts.append(nested)
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
    return ""


def truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n\n[truncated {omitted} characters]"


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern, replacement in SENSITIVE_JSON_FIELD_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _session_title(events: list[dict[str, Any]], path: Path) -> str:
    for event in events:
        if event.get("kind") != "message" or event.get("role") != "user":
            continue
        text = str(event.get("text") or "").strip()
        if not text or text.startswith("<environment_context>"):
            continue
        return _compact_title(text)
    for event in events:
        if event.get("kind") == "message":
            text = str(event.get("text") or "").strip()
            if text:
                return _compact_title(text)
    return path.stem


def _compact_title(text: str, limit: int = 90) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _id_from_filename(path: Path) -> str:
    stem = path.stem
    if "-" in stem:
        return stem.rsplit("-", 1)[-1]
    return stem
