# Persistent Twitch Channel Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep Twitch channel tasks alive across offline/live cycles with independently configurable waiting and live polling intervals.

**Architecture:** Extend the existing `Monitor` loop with an explicit channel phase and interval selector while leaving `tick()` as the source of stream transitions and data writes. Persist the selected phase and interval metadata in heartbeat, and keep old task payloads compatible through `poll_interval_seconds` fallback.

**Tech Stack:** Python 3.10+, `unittest`, file-backed state, vanilla HTML/JavaScript.

**Spec:** `docs/superpowers/specs/2026-10-30-persistent-channel-watch-design.md`

## Global Constraints

- Channel tasks stop only through pause, stop, delete, or process termination.
- Waiting checks never append CCV raw/CSV samples.
- Both intervals default to 30 seconds and clamp to at least 5 seconds.
- Old `poll_interval_seconds` tasks remain valid.
- Existing Twitch game and dual-channel behavior remains compatible.

## Review Focus

- A channel that is offline from task creation must remain running indefinitely.
- A transient single empty response during a live stream must not switch to waiting.
- A second consecutive empty response must switch to waiting without ending the task.
- A new stream after waiting must create and sample its new stream ID.
- Pause/stop flags must remain responsive even during a long configured wait.

---

### Task 1: Interval configuration contract

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

**Interfaces:**
- Produces task keys `watch_interval_seconds: int`, `live_interval_seconds: int`, and compatibility key `poll_interval_seconds: int`.

- [ ] Write failing tests for defaults, custom values, minimum clamps, and old-task fallback in `_api_cfg()`.
- [ ] Verify focused failures.
- [ ] Implement normalized task creation and config propagation.
- [ ] Run focused and full tests.

### Task 2: Persistent channel state machine

**Files:**
- Modify: `monitor.py`
- Create: `tests/test_monitor_watch.py`

**Interfaces:**
- Produces: `Monitor.current_phase() -> str`, `Monitor.current_interval_seconds() -> int`, and persistent channel `run()` behavior.
- Updates heartbeat with `phase`, `watch_interval_seconds`, `live_interval_seconds`, and `next_interval_seconds`.

- [ ] Write failing unit tests for waiting/live interval selection, two-empty confirmation, return to waiting, and duration non-termination for channel tasks.
- [ ] Run focused tests and confirm missing behavior.
- [ ] Implement the smallest state machine and interruptible waiting.
- [ ] Run focused and full tests.

### Task 3: Twitch-only dashboard controls and documentation

**Files:**
- Modify: `server.py`
- Modify: `README.md`
- Modify: `config.json`
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes the two task interval keys and heartbeat `phase`.
- Produces two numeric controls and waiting-state task copy.

- [ ] Write failing rendered-HTML tests for both controls, defaults, payload keys, and removal of the auto-stop checkbox/copy.
- [ ] Verify focused failures.
- [ ] Implement the UI and documentation/config updates.
- [ ] Run the full suite, syntax checks, XLSX smoke test, repository-surface checks, and rendered browser QA.
