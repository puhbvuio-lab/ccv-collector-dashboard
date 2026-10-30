# Remove Built-in YouTube Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove every built-in YouTube collection path while leaving a safe, configurable dashboard link to an independent future tool.

**Architecture:** Keep the Twitch `TaskManager` and dashboard intact. Replace YouTube task/runtime branches with an explicit unsupported-state migration and inject one validated HTTP(S) external URL into the static dashboard.

**Tech Stack:** Python 3.10+, `unittest`, vanilla HTML/JavaScript, JSON configuration.

**Spec:** `docs/superpowers/specs/2026-10-30-remove-youtube-collector-design.md`

## Global Constraints

- Do not delete ignored user runtime data under `data/` or `输出/`.
- Preserve Twitch API collection, Twitch web dual mode, reporting, trends, and exports.
- Do not start, probe, or exchange data with the external YouTube tool.
- Accept only `http://` and `https://` jump URLs.

## Review Focus

- A `javascript:`, `file:`, relative, or credential-bearing URL must not produce a clickable button.
- A persisted YouTube task marked `running` must not restart after upgrade.
- New non-Twitch task payloads must fail without creating task files or threads.
- Twitch channel, game, and dual task configuration must remain unchanged.
- Removed YouTube files and documentation must leave no executable collection reference behind.

---

### Task 1: External jump button contract

**Files:**
- Modify: `server.py`
- Modify: `config.json`
- Modify: `tests/test_server.py`

**Interfaces:**
- Produces: `normalize_external_tool_url(value: object) -> str`
- Produces: `build_index_html(youtube_tool_url: str) -> str`

- [ ] Write failing tests for valid HTTP(S), empty, relative, credential-bearing, and unsafe-scheme URLs.
- [ ] Run focused tests and confirm the missing interface fails.
- [ ] Implement URL normalization and safe button rendering.
- [ ] Run focused and full tests.

### Task 2: Remove YouTube task lifecycle

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: existing `TaskManager.create()` and `TaskManager.load()`.
- Produces: Twitch-only task creation and `unsupported` migration for persisted non-Twitch tasks.

- [ ] Write failing tests that reject new YouTube tasks and prevent persisted YouTube restart.
- [ ] Run focused tests and confirm the current behavior fails.
- [ ] Remove YouTube parser, API collector, worker/config branches, credentials, and UI task options.
- [ ] Run focused and full tests, including existing Twitch lifecycle tests.

### Task 3: Remove repository YouTube assets and documentation

**Files:**
- Delete: `yt_web_pilot.js`
- Delete: `examples/yt_7RWSqGjsSNc_网页观众数_10min.png`
- Delete: `examples/yt_7RWSqGjsSNc_网页实时CCV_数据图表_20260806_185943.xlsx`
- Modify: `.env.example`
- Modify: `package.json`
- Modify: `README.md`
- Delete or update: `docs/ccv-monitor-workflow.drawio`, `docs/ccv-monitor-workflow.drawio.png`
- Create: `tests/test_youtube_removal.py`

**Interfaces:**
- Produces: Twitch-only repository surface plus the documented `youtube_tool_url` jump setting.

- [ ] Write a failing repository-surface test that detects executable YouTube collector assets/references while allowing the external button/config documentation.
- [ ] Run it and verify current assets fail.
- [ ] Remove assets and rewrite documentation/configuration.
- [ ] Run full tests, Python/Node syntax checks, XLSX smoke test, and diff checks.
