from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

import runtime_state
from attack_runtime.spell_modes import spell_mode_label
from bot_config_schema import (
    category_meta,
    format_setting_value,
    get_setting_meta,
    get_setting_value,
    set_setting_value,
)
from telegram_ui.process_controller import BotProcessController


PANEL_HOST = "127.0.0.1"
PANEL_PORT = 8765

_VISIBLE_SETTINGS: dict[str, tuple[str, ...]] = {
    "attack": (
        "START_DELAY_SECONDS",
        "SEARCH_WAIT_SPACE",
        "SEARCH_WAIT_E",
        "SEARCH_WAIT_I",
        "SURRENDER_WAIT",
    ),
    "loot": (
        "ENABLE_BATTLE_GOLD_FILTER",
        "BATTLE_GOLD_MIN",
        "BATTLE_ELIXIR_MIN",
        "BATTLE_GOLD_REROLL_SLEEP",
        "BATTLE_GOLD_OCR_MAX_REROLLS",
    ),
    "spells": (
        "SPELL_MODE",
        "SPELL_COUNT",
        "SPELL_INTERVAL",
    ),
    "wall": (
        "WALL_KEY_CYCLE_ENABLED",
        "WALL_KEY_CYCLE_EVERY_ATTACKS",
        "WALL_KEY_CYCLE_DURATION_SECONDS",
    ),
    "storage": (
        "ENABLE_STORAGE_MONITOR",
        "STORAGE_MONITOR_EVERY_ATTACKS",
        "STORAGE_MONITOR_THRESHOLD",
    ),
    "recovery": (
        "ENABLE_AUTO_RECOVERY",
        "RECOVERY_MAX_LOOP_SECONDS",
        "RECOVERY_NO_PROGRESS_SECONDS",
        "RECOVERY_STALE_SCREEN_SECONDS",
        "RECOVERY_MAX_ATTEMPTS_PER_WINDOW",
    ),
    "screen": (
        "IMAGE_MATCH_CONFIDENCE",
        "WAIT_FOR_IMAGE_TIMEOUT_SECONDS",
        "SEARCH_BUTTON_CHECK_INTERVAL_SECONDS",
        "ARMY_READY_CHECK_INTERVAL_SECONDS",
        "GO_HOME_CHECK_INTERVAL_SECONDS",
    ),
}


INDEX_HTML = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>COC Bot Control</title>
  <style>
    :root {
      --paper: #f5f0e6;
      --ink: #17211d;
      --muted: #66736c;
      --line: rgba(23, 33, 29, 0.14);
      --accent: #1f8f5f;
      --accent-strong: #0d5d3a;
      --accent-soft: rgba(31, 143, 95, 0.12);
      --danger: #b44f3a;
      --danger-soft: rgba(180, 79, 58, 0.12);
      --terminal: #101513;
      --terminal-ink: #9af7bd;
      --shadow: 0 20px 60px rgba(29, 41, 35, 0.12);
      --radius: 24px;
    }

    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    body {
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(31, 143, 95, 0.10), transparent 26%),
        radial-gradient(circle at bottom right, rgba(180, 79, 58, 0.08), transparent 22%),
        linear-gradient(180deg, #f8f4ea 0%, var(--paper) 100%);
    }

    .shell {
      width: min(1200px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.3fr 0.9fr;
      gap: 28px;
      align-items: stretch;
    }

    .poster,
    .terminal,
    .settings,
    .summary {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .poster {
      background:
        linear-gradient(135deg, rgba(255,255,255,0.72), rgba(255,255,255,0.42)),
        linear-gradient(140deg, #f6efe0 0%, #f0e7d6 100%);
      padding: 32px;
      position: relative;
      min-height: 340px;
    }

    .poster::after {
      content: "";
      position: absolute;
      inset: auto -8% -28% auto;
      width: 260px;
      height: 260px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(31, 143, 95, 0.26), transparent 68%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.58);
      border: 1px solid rgba(23, 33, 29, 0.10);
      font-family: "Menlo", "Monaco", "IBM Plex Mono", monospace;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--muted);
      transition: background 160ms ease, box-shadow 160ms ease;
    }

    .dot.running {
      background: var(--accent);
      box-shadow: 0 0 0 6px rgba(31, 143, 95, 0.16);
    }

    h1 {
      margin: 20px 0 12px;
      font-size: clamp(44px, 7vw, 76px);
      line-height: 0.94;
      letter-spacing: -0.05em;
      max-width: 8ch;
    }

    .lead {
      max-width: 40ch;
      margin: 0;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.55;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 28px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 14px 20px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease, background 120ms ease;
    }

    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.45; cursor: wait; transform: none; }

    .primary { background: var(--accent); color: #f4fffa; }
    .danger { background: #f6e1dc; color: var(--danger); }
    .ghost { background: rgba(255,255,255,0.66); color: var(--ink); border: 1px solid rgba(23, 33, 29, 0.10); }

    .summary {
      margin-top: 28px;
      background: rgba(255,255,255,0.48);
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .metric {
      padding: 18px 20px;
      border-right: 1px solid var(--line);
    }
    .metric:last-child { border-right: 0; }

    .metric-label {
      font-family: "Menlo", "Monaco", "IBM Plex Mono", monospace;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }

    .metric-value {
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
    }

    .terminal {
      background: linear-gradient(180deg, #151d19 0%, var(--terminal) 100%);
      color: var(--terminal-ink);
      padding: 22px 24px 24px;
      display: flex;
      flex-direction: column;
      min-height: 340px;
    }

    .terminal-head {
      display: flex;
      gap: 8px;
      margin-bottom: 22px;
    }

    .terminal-head span {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: rgba(255,255,255,0.22);
    }

    .terminal-screen {
      font-family: "Menlo", "Monaco", "IBM Plex Mono", monospace;
      font-size: 14px;
      line-height: 1.7;
      white-space: pre-wrap;
      flex: 1;
    }

    .terminal-line::after {
      content: "_";
      animation: blink 1s steps(1, end) infinite;
      margin-left: 2px;
    }

    @keyframes blink {
      50% { opacity: 0; }
    }

    .layout {
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
      margin-top: 28px;
    }

    .settings {
      background: rgba(255,255,255,0.64);
      padding: 24px;
    }

    .settings-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 18px;
    }

    .settings-head h2 {
      margin: 0;
      font-size: 28px;
      letter-spacing: -0.04em;
    }

    .settings-note {
      color: var(--muted);
      font-size: 14px;
    }

    .groups {
      display: grid;
      gap: 18px;
    }

    .group {
      border-top: 1px solid var(--line);
      padding-top: 18px;
    }

    .group:first-child {
      border-top: 0;
      padding-top: 0;
    }

    .group-title {
      margin: 0 0 12px;
      font-size: 20px;
    }

    .group-description {
      margin: 0 0 16px;
      color: var(--muted);
      line-height: 1.45;
    }

    .setting-row {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(180px, 0.7fr) auto;
      gap: 14px;
      align-items: center;
      padding: 12px 0;
      border-top: 1px solid rgba(23, 33, 29, 0.08);
    }

    .setting-row:first-of-type { border-top: 0; }

    .setting-name {
      font-weight: 700;
      margin-bottom: 4px;
    }

    .setting-description {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }

    .field,
    select {
      width: 100%;
      border-radius: 14px;
      border: 1px solid rgba(23, 33, 29, 0.12);
      background: rgba(255,255,255,0.72);
      padding: 12px 14px;
      font: inherit;
      color: var(--ink);
    }

    .toggle-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
    }

    .flash {
      position: sticky;
      top: 16px;
      z-index: 20;
      margin-left: auto;
      width: fit-content;
      max-width: min(460px, 100%);
      padding: 12px 16px;
      border-radius: 16px;
      background: rgba(255,255,255,0.92);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      opacity: 0;
      transform: translateY(-10px);
      pointer-events: none;
      transition: opacity 160ms ease, transform 160ms ease;
      font-family: "Menlo", "Monaco", "IBM Plex Mono", monospace;
      font-size: 13px;
    }

    .flash.show {
      opacity: 1;
      transform: translateY(0);
    }

    .flash.error {
      border-color: rgba(180, 79, 58, 0.24);
      background: #fff3ef;
      color: var(--danger);
    }

    @media (max-width: 960px) {
      .hero { grid-template-columns: 1fr; }
      .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .setting-row { grid-template-columns: 1fr; }
    }

    @media (max-width: 640px) {
      .shell { width: min(100vw - 20px, 1200px); padding-top: 18px; }
      .poster, .terminal, .settings { border-radius: 20px; }
      .poster { padding: 24px; min-height: auto; }
      .summary { grid-template-columns: 1fr; }
      h1 { max-width: 10ch; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div id="flash" class="flash"></div>

    <section class="hero">
      <div class="poster">
        <div class="eyebrow">
          <span id="status-dot" class="dot"></span>
          <span id="status-chip">STOPPED</span>
        </div>
        <h1>COC bot control room</h1>
        <p class="lead">
          Локальная панель управления первым ботом: быстрый старт, безопасная остановка и только те параметры,
          которые реально влияют на стабильность.
        </p>

        <div class="actions">
          <button id="start-btn" class="primary">Запустить бота</button>
          <button id="stop-btn" class="danger">Остановить бота</button>
          <button id="refresh-btn" class="ghost">Обновить статус</button>
        </div>

        <div class="summary">
          <div class="metric">
            <div class="metric-label">Process</div>
            <div id="metric-process" class="metric-value">offline</div>
          </div>
          <div class="metric">
            <div class="metric-label">PID</div>
            <div id="metric-pid" class="metric-value">—</div>
          </div>
          <div class="metric">
            <div class="metric-label">Attacks</div>
            <div id="metric-attacks" class="metric-value">0</div>
          </div>
          <div class="metric">
            <div class="metric-label">Profile</div>
            <div id="metric-profile" class="metric-value">default</div>
          </div>
        </div>
      </div>

      <aside class="terminal">
        <div class="terminal-head"><span></span><span></span><span></span></div>
        <div class="terminal-screen">
          <div id="terminal-line" class="terminal-line"></div>
          <div id="terminal-meta"></div>
        </div>
      </aside>
    </section>

    <section class="layout">
      <div class="settings">
        <div class="settings-head">
          <h2>Настройки</h2>
          <div class="settings-note">Сохраняются сразу в runtime overrides.</div>
        </div>
        <div id="groups" class="groups"></div>
      </div>
    </section>
  </div>

  <script>
    const state = {
      status: null,
      settings: [],
      terminalIndex: 0,
      terminalTimer: null,
    };

    const els = {
      flash: document.getElementById("flash"),
      statusDot: document.getElementById("status-dot"),
      statusChip: document.getElementById("status-chip"),
      process: document.getElementById("metric-process"),
      pid: document.getElementById("metric-pid"),
      attacks: document.getElementById("metric-attacks"),
      profile: document.getElementById("metric-profile"),
      terminalLine: document.getElementById("terminal-line"),
      terminalMeta: document.getElementById("terminal-meta"),
      groups: document.getElementById("groups"),
      start: document.getElementById("start-btn"),
      stop: document.getElementById("stop-btn"),
      refresh: document.getElementById("refresh-btn"),
    };

    function showFlash(text, isError = false) {
      els.flash.textContent = text;
      els.flash.classList.toggle("error", isError);
      els.flash.classList.add("show");
      clearTimeout(showFlash.timer);
      showFlash.timer = setTimeout(() => els.flash.classList.remove("show"), 2600);
    }

    async function requestJson(url, options = {}) {
      const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Request failed");
      }
      return payload;
    }

    function terminalFrames(status) {
      if (!status) {
        return ["[panel] waiting for state"];
      }
      if (status.running) {
        return [
          `[engine] status: RUNNING    | polling visual guards`,
          `[engine] status: RUNNING.   | tracking battle loop`,
          `[engine] status: RUNNING..  | watching recovery signals`,
          `[engine] status: RUNNING... | holding process steady`,
        ];
      }
      return [
        `[engine] status: STOPPED    | idle`,
        `[engine] status: STOPPED.   | awaiting operator command`,
        `[engine] status: STOPPED..  | safe to adjust settings`,
      ];
    }

    function renderTerminal() {
      const frames = terminalFrames(state.status);
      const frame = frames[state.terminalIndex % frames.length];
      els.terminalLine.textContent = frame;
      if (state.status) {
        const recovery = state.status.last_recovery_time
          ? `${state.status.last_recovery_issue_code || "recovery"} @ ${state.status.last_recovery_time}`
          : "no recent recovery events";
        els.terminalMeta.textContent = `spell=${state.status.spell_mode_label} | wall=${state.status.wall_cycle_enabled ? "on" : "off"} | ${recovery}`;
      }
      state.terminalIndex += 1;
    }

    function renderStatus(status) {
      state.status = status;
      els.statusDot.classList.toggle("running", status.running);
      els.statusChip.textContent = status.running ? "RUNNING" : "STOPPED";
      els.process.textContent = status.running ? "online" : "offline";
      els.pid.textContent = status.pid || "—";
      els.attacks.textContent = String(status.attack_count);
      els.profile.textContent = status.input_profile;
      renderTerminal();
    }

    function inputControl(setting) {
      if (setting.type === "bool") {
        return `
          <label class="toggle-wrap">
            <input data-setting-id="${setting.id}" type="checkbox" ${setting.value ? "checked" : ""}>
            <span>${setting.formatted_value}</span>
          </label>
        `;
      }
      if (setting.type === "enum") {
        return `
          <select data-setting-id="${setting.id}">
            ${setting.choices.map((choice) => `<option value="${choice}" ${choice === setting.value ? "selected" : ""}>${choice}</option>`).join("")}
          </select>
        `;
      }
      return `<input class="field" data-setting-id="${setting.id}" type="text" value="${setting.raw_display}">`;
    }

    function renderSettings(groups) {
      state.settings = groups;
      els.groups.innerHTML = groups.map((group) => `
        <section class="group">
          <h3 class="group-title">${group.label}</h3>
          <p class="group-description">${group.description}</p>
          ${group.settings.map((setting) => `
            <div class="setting-row">
              <div>
                <div class="setting-name">${setting.icon} ${setting.label}</div>
                <p class="setting-description">${setting.description}</p>
              </div>
              <div>${inputControl(setting)}</div>
              <div><button class="ghost" data-save-id="${setting.id}">Сохранить</button></div>
            </div>
          `).join("")}
        </section>
      `).join("");
    }

    function readInputValue(settingId) {
      const setting = state.settings.flatMap((group) => group.settings).find((item) => item.id === settingId);
      const node = document.querySelector(`[data-setting-id="${settingId}"]`);
      if (!setting || !node) {
        throw new Error("Setting input not found");
      }
      if (setting.type === "bool") {
        return node.checked;
      }
      return node.value;
    }

    async function refreshStatus() {
      const payload = await requestJson("/api/status");
      renderStatus(payload);
    }

    async function refreshSettings() {
      const payload = await requestJson("/api/settings");
      renderSettings(payload.groups);
    }

    async function refreshAll() {
      await Promise.all([refreshStatus(), refreshSettings()]);
    }

    async function saveSetting(settingId) {
      const value = readInputValue(settingId);
      await requestJson(`/api/settings/${settingId}`, {
        method: "POST",
        body: JSON.stringify({ value }),
      });
      showFlash(`Сохранено: ${settingId}`);
      await refreshAll();
    }

    async function startBot() {
      els.start.disabled = true;
      try {
        const payload = await requestJson("/api/start", { method: "POST" });
        showFlash(payload.message);
        await refreshStatus();
      } catch (error) {
        showFlash(error.message, true);
      } finally {
        els.start.disabled = false;
      }
    }

    async function stopBot() {
      els.stop.disabled = true;
      try {
        const payload = await requestJson("/api/stop", { method: "POST" });
        showFlash(payload.message);
        await refreshStatus();
      } catch (error) {
        showFlash(error.message, true);
      } finally {
        els.stop.disabled = false;
      }
    }

    document.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-save-id]");
      if (!button) {
        return;
      }
      button.disabled = true;
      try {
        await saveSetting(button.dataset.saveId);
      } catch (error) {
        showFlash(error.message, true);
      } finally {
        button.disabled = false;
      }
    });

    els.start.addEventListener("click", startBot);
    els.stop.addEventListener("click", stopBot);
    els.refresh.addEventListener("click", async () => {
      try {
        await refreshAll();
        showFlash("Статус обновлен");
      } catch (error) {
        showFlash(error.message, true);
      }
    });

    async function boot() {
      try {
        await refreshAll();
      } catch (error) {
        showFlash(error.message, true);
      }
      clearInterval(state.terminalTimer);
      state.terminalTimer = setInterval(renderTerminal, 1000);
      setInterval(refreshStatus, 1000);
    }

    boot();
  </script>
</body>
</html>
"""


@dataclass
class PanelStatus:
    running: bool
    pid: int | None
    attack_count: int
    input_profile: str
    current_account: str
    spell_mode: str
    spell_mode_label: str
    wall_cycle_enabled: bool
    wall_cycle_every: int
    last_recovery_issue_code: str | None
    last_recovery_details: str | None
    last_recovery_time: str | None
    updated_at: str


@dataclass
class SettingPayload:
    id: str
    icon: str
    label: str
    description: str
    type: str
    value: Any
    raw_display: str
    formatted_value: str
    choices: list[str]


class ControlPanelService:
    def __init__(self) -> None:
        self.controller = BotProcessController()

    def build_status(self) -> PanelStatus:
        recovery = runtime_state.get_last_recovery_event()
        pid = self.controller.running_pid()
        spell_mode = runtime_state.get_spell_mode(default="stoneDick")
        return PanelStatus(
            running=pid is not None,
            pid=pid,
            attack_count=int(runtime_state.load_state().get("attack_count", 0)),
            input_profile=runtime_state.get_input_profile(default="default"),
            current_account=runtime_state.get_current_account() or "не определен",
            spell_mode=spell_mode,
            spell_mode_label=spell_mode_label(spell_mode),
            wall_cycle_enabled=runtime_state.wall_key_cycle_enabled(default=True),
            wall_cycle_every=runtime_state.get_wall_key_cycle_every_override(default=20),
            last_recovery_issue_code=recovery.get("issue_code"),
            last_recovery_details=recovery.get("issue_details"),
            last_recovery_time=recovery.get("time"),
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )

    def settings_payload(self) -> dict[str, Any]:
        groups: list[dict[str, Any]] = []
        for category_id, setting_ids in _VISIBLE_SETTINGS.items():
            meta = category_meta(category_id)
            settings = [self._setting_payload(setting_id) for setting_id in setting_ids]
            groups.append(
                {
                    "id": category_id,
                    "label": meta["label"],
                    "description": meta["description"],
                    "settings": [asdict(setting) for setting in settings],
                }
            )
        return {"groups": groups}

    def _setting_payload(self, setting_id: str) -> SettingPayload:
        meta = get_setting_meta(setting_id)
        value = get_setting_value(setting_id)
        if meta["type"] == "bool":
            raw_display = "true" if bool(value) else "false"
        elif value is None:
            raw_display = ""
        elif isinstance(value, tuple):
            raw_display = ",".join(str(item) for item in value)
        else:
            raw_display = str(value)
        return SettingPayload(
            id=setting_id,
            icon=str(meta["icon"]),
            label=str(meta["label"]),
            description=str(meta["description"]),
            type=str(meta["type"]),
            value=value,
            raw_display=raw_display,
            formatted_value=format_setting_value(setting_id, value),
            choices=[str(item) for item in meta.get("choices", ())],
        )

    def start_bot(self) -> dict[str, Any]:
        ok, message = self.controller.start()
        if not ok:
            raise ValueError(message)
        return {"message": message}

    def stop_bot(self) -> dict[str, Any]:
        ok, message = self.controller.stop()
        if not ok:
            raise ValueError(message)
        return {"message": message}

    def update_setting(self, setting_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if setting_id not in {item for group in _VISIBLE_SETTINGS.values() for item in group}:
            raise KeyError(f"Unknown setting: {setting_id}")
        if "value" not in payload:
            raise ValueError("Missing 'value'")
        value = payload["value"]
        if isinstance(value, bool):
            raw_value = "true" if value else "false"
        else:
            raw_value = str(value)
        applied = set_setting_value(setting_id, raw_value)
        return {
            "setting_id": setting_id,
            "applied": applied,
            "formatted": format_setting_value(setting_id),
        }


class ControlPanelHandler(BaseHTTPRequestHandler):
    service = ControlPanelService()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._respond_html(INDEX_HTML)
            return
        if path == "/api/status":
            self._respond_json(asdict(self.service.build_status()))
            return
        if path == "/api/settings":
            self._respond_json(self.service.settings_payload())
            return
        self._respond_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/start":
                self._respond_json(self.service.start_bot())
                return
            if path == "/api/stop":
                self._respond_json(self.service.stop_bot())
                return
            if path.startswith("/api/settings/"):
                setting_id = path.rsplit("/", 1)[-1]
                payload = self._read_json_body()
                self._respond_json(self.service.update_setting(setting_id, payload))
                return
            self._respond_error(HTTPStatus.NOT_FOUND, "Not found")
        except KeyError as exc:
            self._respond_error(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            self._respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - defensive API guard
            self._respond_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        if not raw:
            return {}
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def _respond_html(self, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _respond_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _respond_error(self, status: HTTPStatus, message: str) -> None:
        self._respond_json({"error": str(message)}, status=status)


def run_control_panel_server(host: str = PANEL_HOST, port: int = PANEL_PORT) -> None:
    server = ThreadingHTTPServer((host, port), ControlPanelHandler)
    print(f"control panel running at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def project_dir() -> str:
    return os.path.dirname(__file__)
