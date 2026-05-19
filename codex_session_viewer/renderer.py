from __future__ import annotations

import html
import json
from typing import Any


def render_html(sessions: list[dict[str, Any]], title: str = "Codex Sessions") -> str:
    escaped_title = html.escape(title, quote=True)
    session_json = _safe_json(sessions)
    return (
        HTML_TEMPLATE.replace("__TITLE__", escaped_title)
        .replace("__SESSION_JSON__", session_json)
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <style>
    :root {
      color-scheme: dark light;
      --bg: #0b0d10;
      --bg-soft: #11151a;
      --sidebar: #12161d;
      --panel: #171c23;
      --panel-strong: #1d242d;
      --text: #ecf1f7;
      --muted: #9ba8b8;
      --faint: #6d7a8c;
      --line: #2a333f;
      --line-soft: #202833;
      --accent: #62d6c5;
      --accent-strong: #2dd4bf;
      --accent-soft: rgba(45, 212, 191, 0.13);
      --user: #1d3b37;
      --assistant: #171c23;
      --tool: #141920;
      --warning: #f59e0b;
      --danger-soft: rgba(245, 158, 11, 0.12);
      --code-bg: #080a0d;
      --code-text: #dbe7f3;
      --shadow: 0 18px 42px rgba(0, 0, 0, 0.3);
      --radius: 8px;
    }
    @media (prefers-color-scheme: light) {
      :root {
        --bg: #f3f5f8;
        --bg-soft: #eef1f5;
        --sidebar: #ffffff;
        --panel: #ffffff;
        --panel-strong: #f8fafc;
        --text: #18202b;
        --muted: #647386;
        --faint: #8793a3;
        --line: #d9e0ea;
        --line-soft: #e7ecf2;
        --accent: #0f766e;
        --accent-strong: #0d9488;
        --accent-soft: rgba(13, 148, 136, 0.1);
        --user: #e3f5f1;
        --assistant: #ffffff;
        --tool: #f7f9fc;
        --warning: #b45309;
        --danger-soft: rgba(245, 158, 11, 0.14);
        --code-bg: #101820;
        --code-text: #e8eef5;
        --shadow: 0 18px 34px rgba(24, 32, 43, 0.08);
      }
    }
    * { box-sizing: border-box; }
    html { min-height: 100%; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(45, 212, 191, 0.12), transparent 28rem),
        linear-gradient(135deg, var(--bg), var(--bg-soft));
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      letter-spacing: 0;
    }
    button, input, select {
      font: inherit;
    }
    button {
      color: inherit;
    }
    .app-shell {
      display: grid;
      grid-template-columns: minmax(300px, 388px) minmax(0, 1fr);
      min-height: 100vh;
    }
    .sidebar {
      min-width: 0;
      background: color-mix(in srgb, var(--sidebar) 96%, transparent);
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      box-shadow: 10px 0 30px rgba(0, 0, 0, 0.1);
    }
    .sidebar-top {
      padding: 18px 16px 14px;
      border-bottom: 1px solid var(--line-soft);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
      margin-bottom: 16px;
    }
    .brand-mark {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: linear-gradient(145deg, var(--accent), #7dd3fc);
      color: #06110f;
      font-weight: 800;
      box-shadow: 0 10px 24px rgba(45, 212, 191, 0.22);
      flex: 0 0 auto;
    }
    h1 {
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
      font-weight: 760;
      overflow-wrap: anywhere;
    }
    .brand-subtitle {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.3;
    }
    .controls {
      display: grid;
      gap: 9px;
    }
    .control-field {
      position: relative;
    }
    .control-field span {
      position: absolute;
      left: 11px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--faint);
      font-size: 12px;
      pointer-events: none;
    }
    input, select {
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 8px 10px;
      background: var(--panel);
      color: var(--text);
      outline: none;
    }
    input {
      padding-left: 31px;
    }
    input:focus, select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }
    .stat-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--line-soft);
    }
    .stat-pill {
      min-width: 0;
      border: 1px solid var(--line-soft);
      border-radius: var(--radius);
      padding: 8px 9px;
      background: var(--panel);
    }
    .stat-value {
      display: block;
      font-weight: 760;
      font-size: 15px;
      line-height: 1.2;
    }
    .stat-label {
      display: block;
      margin-top: 2px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.2;
    }
    .session-summary {
      padding: 0 16px 12px;
      color: var(--muted);
      font-size: 12px;
    }
    .sessions {
      overflow: auto;
      flex: 1;
      padding: 8px;
    }
    .session-button {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 10px;
      width: 100%;
      border: 1px solid transparent;
      border-radius: var(--radius);
      background: transparent;
      color: var(--text);
      text-align: left;
      padding: 10px;
      cursor: pointer;
      transition: border-color 140ms ease, background 140ms ease, transform 140ms ease;
    }
    .session-button:hover {
      background: color-mix(in srgb, var(--panel) 76%, transparent);
      border-color: var(--line-soft);
    }
    .session-button.active {
      background: var(--accent-soft);
      border-color: color-mix(in srgb, var(--accent) 55%, var(--line));
      box-shadow: inset 3px 0 0 var(--accent);
    }
    .session-avatar {
      width: 34px;
      height: 34px;
      border-radius: var(--radius);
      display: grid;
      place-items: center;
      background: var(--panel-strong);
      color: var(--accent);
      font-weight: 760;
      border: 1px solid var(--line-soft);
      text-transform: uppercase;
    }
    .session-main {
      min-width: 0;
    }
    .session-title {
      display: block;
      font-weight: 680;
      line-height: 1.25;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .session-cwd {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.3;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .session-foot {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
      color: var(--faint);
      font-size: 11px;
      line-height: 1.2;
    }
    .mini-pill {
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 3px 7px;
      background: color-mix(in srgb, var(--panel) 78%, transparent);
    }
    .workspace {
      min-width: 0;
      display: flex;
      flex-direction: column;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent 13rem),
        transparent;
    }
    .conversation-header {
      position: sticky;
      top: 0;
      z-index: 2;
      padding: 16px 24px;
      background: color-mix(in srgb, var(--bg) 88%, transparent);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--line-soft);
    }
    .conversation-kicker {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 7px;
    }
    .live-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 4px var(--accent-soft);
    }
    .conversation-header h2 {
      margin: 0;
      max-width: 1050px;
      font-size: 21px;
      line-height: 1.25;
      font-weight: 760;
      overflow-wrap: anywhere;
    }
    .conversation-meta {
      margin-top: 9px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    .meta-chip {
      max-width: 100%;
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 4px 9px;
      background: color-mix(in srgb, var(--panel) 76%, transparent);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .chat-feed {
      width: min(100%, 1060px);
      padding: 22px 24px 56px;
    }
    .message-row {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 12px;
      margin: 0 0 16px;
    }
    .message-row.user {
      grid-template-columns: minmax(0, 1fr) 34px;
      margin-left: min(8vw, 92px);
    }
    .message-row.assistant,
    .message-row.agent_message {
      margin-right: min(7vw, 84px);
    }
    .message-icon {
      width: 34px;
      height: 34px;
      border-radius: var(--radius);
      display: grid;
      place-items: center;
      background: var(--panel);
      border: 1px solid var(--line-soft);
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
    }
    .message-row.user .message-icon {
      grid-column: 2;
      grid-row: 1;
      background: var(--accent-soft);
    }
    .message-content {
      min-width: 0;
    }
    .message-row.user .message-content {
      grid-column: 1;
      grid-row: 1;
    }
    .message-meta {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin: 0 0 5px;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 720;
    }
    .message-bubble {
      border: 1px solid var(--line-soft);
      border-radius: var(--radius);
      background: var(--assistant);
      box-shadow: var(--shadow);
      padding: 13px 14px;
      line-height: 1.58;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .message-row.user .message-bubble {
      background: var(--user);
      border-color: color-mix(in srgb, var(--accent) 36%, var(--line));
    }
    .tool-card {
      margin: 0 0 14px 46px;
      border: 1px solid var(--line-soft);
      border-radius: var(--radius);
      background: var(--tool);
      overflow: hidden;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
    }
    .tool-card.output {
      margin-left: 78px;
      background: color-mix(in srgb, var(--tool) 88%, var(--panel));
    }
    .tool-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line-soft);
      color: var(--muted);
      font-size: 12px;
    }
    .tool-title {
      min-width: 0;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 720;
      color: var(--text);
    }
    .tool-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent);
      flex: 0 0 auto;
    }
    .tool-call-id {
      color: var(--faint);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    details.tool-output {
      margin: 0;
      padding: 0;
    }
    details.tool-output summary {
      cursor: pointer;
      list-style: none;
      padding: 12px;
      color: var(--accent);
      font-weight: 720;
    }
    details.tool-output summary::-webkit-details-marker {
      display: none;
    }
    details.tool-output summary::before {
      content: "Show output";
    }
    details.tool-output[open] summary::before {
      content: "Hide output";
    }
    pre {
      margin: 0;
      max-height: 560px;
      overflow: auto;
      padding: 13px 14px;
      background: var(--code-bg);
      color: var(--code-text);
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: 12px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .parse-error {
      background: var(--danger-soft);
      border-color: color-mix(in srgb, var(--warning) 48%, var(--line));
    }
    .empty {
      margin: 24px;
      border: 1px dashed var(--line);
      border-radius: var(--radius);
      padding: 22px;
      color: var(--muted);
      background: color-mix(in srgb, var(--panel) 72%, transparent);
    }
    .warning {
      color: var(--warning);
      font-weight: 720;
    }
    @media (max-width: 840px) {
      .app-shell {
        grid-template-columns: 1fr;
      }
      .sidebar {
        min-height: 42vh;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .chat-feed {
        padding: 16px 12px 38px;
      }
      .conversation-header {
        padding: 14px 12px;
      }
      .message-row,
      .message-row.user,
      .message-row.assistant,
      .message-row.agent_message {
        margin-left: 0;
        margin-right: 0;
      }
      .tool-card,
      .tool-card.output {
        margin-left: 0;
      }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-top">
        <div class="brand">
          <div class="brand-mark">C</div>
          <div>
            <h1>__TITLE__</h1>
            <p class="brand-subtitle">Local Codex session history</p>
          </div>
        </div>
        <div class="controls">
          <label class="control-field">
            <span>Search</span>
            <input id="session-search" type="search" placeholder="Prompt, path, or session id">
          </label>
          <select id="cwd-filter" aria-label="Filter by working directory"></select>
        </div>
      </div>
      <div id="stat-strip" class="stat-strip"></div>
      <div id="session-summary" class="session-summary"></div>
      <div id="session-list" class="sessions"></div>
    </aside>
    <main class="workspace">
      <section id="conversation-header" class="conversation-header"></section>
      <section id="timeline" class="chat-feed"></section>
    </main>
  </div>
  <template id="tool-output-template"><details class="tool-output"></details></template>
  <script id="session-data" type="application/json">__SESSION_JSON__</script>
  <script>
    const sessions = JSON.parse(document.getElementById('session-data').textContent || '[]');
    const state = { selectedId: sessions[0]?.id || null, search: '', cwd: 'all' };
    const listEl = document.getElementById('session-list');
    const summaryEl = document.getElementById('session-summary');
    const statStripEl = document.getElementById('stat-strip');
    const headerEl = document.getElementById('conversation-header');
    const timelineEl = document.getElementById('timeline');
    const searchEl = document.getElementById('session-search');
    const cwdEl = document.getElementById('cwd-filter');

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function shortTime(value) {
      if (!value) return '';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString();
    }

    function shortDate(value) {
      if (!value) return '';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }

    function initialFor(session) {
      const source = (session.title || session.cwd || session.id || 'C').trim();
      return source[0] || 'C';
    }

    function filteredSessions() {
      const needle = state.search.trim().toLowerCase();
      return sessions.filter((session) => {
        const cwdMatch = state.cwd === 'all' || (session.cwd || '(unknown)') === state.cwd;
        const haystack = [session.title, session.cwd, session.id, session.file_name]
          .join('\\n')
          .toLowerCase();
        return cwdMatch && (!needle || haystack.includes(needle));
      });
    }

    function populateCwdFilter() {
      const cwds = Array.from(new Set(sessions.map((session) => session.cwd || '(unknown)'))).sort();
      cwdEl.innerHTML = '<option value="all">All working directories</option>' +
        cwds.map((cwd) => `<option value="${escapeHtml(cwd)}">${escapeHtml(cwd)}</option>`).join('');
    }

    function renderStatStrip(visible) {
      const messageCount = visible.reduce((total, session) => total + (session.message_count || 0), 0);
      const toolCount = visible.reduce((total, session) => total + (session.tool_call_count || 0), 0);
      statStripEl.innerHTML = `
        <div class="stat-pill"><span class="stat-value">${visible.length}</span><span class="stat-label">Sessions</span></div>
        <div class="stat-pill"><span class="stat-value">${messageCount}</span><span class="stat-label">Messages</span></div>
        <div class="stat-pill"><span class="stat-value">${toolCount}</span><span class="stat-label">Tool calls</span></div>
      `;
    }

    function renderSessionList() {
      const visible = filteredSessions();
      renderStatStrip(visible);
      summaryEl.textContent = `${visible.length} of ${sessions.length} sessions shown`;
      if (!visible.some((session) => session.id === state.selectedId)) {
        state.selectedId = visible[0]?.id || null;
      }
      listEl.innerHTML = visible.map((session) => `
        <button class="session-button ${session.id === state.selectedId ? 'active' : ''}" data-session-id="${escapeHtml(session.id)}">
          <span class="session-avatar">${escapeHtml(initialFor(session))}</span>
          <span class="session-main">
            <span class="session-title">${escapeHtml(session.title || session.id)}</span>
            <span class="session-cwd">${escapeHtml(session.cwd || '(unknown cwd)')}</span>
            <span class="session-foot">
              <span class="mini-pill">${escapeHtml(shortDate(session.updated_at))}</span>
              <span class="mini-pill">${session.message_count || 0} msgs</span>
              <span class="mini-pill">${session.tool_call_count || 0} tools</span>
              ${session.parse_error_count ? `<span class="mini-pill warning">${session.parse_error_count} errors</span>` : ''}
            </span>
          </span>
        </button>
      `).join('') || '<div class="empty">No sessions match the current filters.</div>';
      for (const button of listEl.querySelectorAll('[data-session-id]')) {
        button.addEventListener('click', () => {
          state.selectedId = button.dataset.sessionId;
          render();
        });
      }
    }

    function renderConversation() {
      const session = sessions.find((item) => item.id === state.selectedId);
      if (!session) {
        headerEl.innerHTML = '<div class="conversation-kicker"><span class="live-dot"></span>No session selected</div><h2>Adjust the filters to select a session.</h2>';
        timelineEl.innerHTML = '';
        return;
      }
      headerEl.innerHTML = `
        <div class="conversation-kicker"><span class="live-dot"></span><span>${escapeHtml(shortTime(session.updated_at))}</span></div>
        <h2>${escapeHtml(session.title || session.id)}</h2>
        <div class="conversation-meta">
          <span class="meta-chip">${escapeHtml(session.cwd || '(unknown cwd)')}</span>
          <span class="meta-chip">${escapeHtml(session.file_name || session.id)}</span>
          <span class="meta-chip">${session.message_count || 0} messages</span>
          <span class="meta-chip">${session.tool_call_count || 0} tool calls</span>
        </div>
      `;
      const parseErrors = (session.parse_errors || []).map((error) => `
        <article class="tool-card parse-error">
          <div class="tool-head"><span class="tool-title"><span class="tool-dot"></span>Parse error</span><span>${escapeHtml(error.message)}</span></div>
          <pre>${escapeHtml(error.preview || '')}</pre>
        </article>
      `).join('');
      const events = (session.events || []).map(renderEvent).join('');
      timelineEl.innerHTML = parseErrors + events || '<div class="empty">This session has no renderable events.</div>';
    }

    function renderEvent(event) {
      if (event.kind === 'message' || event.kind === 'agent_message') {
        const role = event.role || event.kind;
        const initials = role === 'user' ? 'U' : 'AI';
        return `
          <article class="message-row ${escapeHtml(role)}">
            <div class="message-icon">${escapeHtml(initials)}</div>
            <div class="message-content">
              <div class="message-meta"><span>${escapeHtml(role)}</span><span>${escapeHtml(shortTime(event.timestamp))}</span></div>
              <div class="message-bubble">${escapeHtml(event.text || '')}</div>
            </div>
          </article>
        `;
      }
      if (event.kind === 'tool_call') {
        return `
          <article class="tool-card">
            <div class="tool-head">
              <span class="tool-title"><span class="tool-dot"></span>${escapeHtml(event.name || 'tool')}</span>
              <span class="tool-call-id">${escapeHtml(event.call_id || '')}</span>
            </div>
            <pre>${escapeHtml(event.arguments || '')}</pre>
          </article>
        `;
      }
      if (event.kind === 'tool_output') {
        return `
          <article class="tool-card output">
            <div class="tool-head">
              <span class="tool-title"><span class="tool-dot"></span>Tool output</span>
              <span class="tool-call-id">${escapeHtml(event.call_id || '')}</span>
            </div>
            <details class="tool-output">
              <summary></summary>
              <pre>${escapeHtml(event.output || '')}</pre>
            </details>
          </article>
        `;
      }
      return '';
    }

    function render() {
      renderSessionList();
      renderConversation();
    }

    searchEl.addEventListener('input', () => {
      state.search = searchEl.value;
      render();
    });
    cwdEl.addEventListener('change', () => {
      state.cwd = cwdEl.value;
      render();
    });
    populateCwdFilter();
    render();
  </script>
</body>
</html>
"""


def _safe_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
