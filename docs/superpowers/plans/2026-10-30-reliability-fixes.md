# CCV Reliability Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate confirmed task lifecycle and installation failures without changing collection data formats or HTTP APIs.

**Architecture:** Keep `TaskManager` and the existing file-backed task registry. Add small deterministic helpers and guarded state transitions that can be exercised without starting network collectors.

**Tech Stack:** Python 3.10+, `unittest`, pathlib, threading, Node syntax checks.

**Spec:** `docs/superpowers/specs/2026-10-30-reliability-fixes-design.md`

## Global Constraints

- Preserve current HTTP endpoints and collection file formats.
- Do not access Twitch or YouTube during tests.
- Do not delete existing runtime data.
- Treat Playwright and `@oai/artifact-tool` as optional runtimes.

## Review Focus

- Two identical tasks created in one second must receive distinct IDs.
- A deletion timeout must not remove a task or its data while its worker remains alive.
- A completed worker may be removed and purged safely.
- Persisted `running` tasks must be distinguishable from live in-process workers.
- A clean Python installation must receive every dependency needed by the built-in XLSX export.

---

### Task 1: Test harness and unique task IDs

**Files:**
- Create: `tests/test_server.py`
- Modify: `server.py`

**Interfaces:**
- Produces: `TaskManager.allocate_task_id(base_id: str) -> str`

- [ ] Write failing tests for repeated base IDs.
- [ ] Run the focused test and confirm collision behavior fails.
- [ ] Implement deterministic suffix allocation under the manager lock.
- [ ] Run the focused and full test suite.

### Task 2: Safe asynchronous deletion

**Files:**
- Modify: `tests/test_server.py`
- Modify: `server.py`

**Interfaces:**
- Produces: `_delete_after_stop(task_id: str, purge: bool) -> bool`

- [ ] Write failing tests for an alive thread after timeout and an exited thread.
- [ ] Verify the unsafe deletion case fails.
- [ ] Preserve the task/data on timeout and expose `delete_failed`; purge only after confirmed exit.
- [ ] Run focused and full tests.

### Task 3: Startup state reconciliation

**Files:**
- Modify: `tests/test_server.py`
- Modify: `server.py`

**Interfaces:**
- Produces: persisted `recovering` transition before a restored worker starts.

- [ ] Write a failing load/recovery state test without network access.
- [ ] Verify it fails against current direct `running` restart behavior.
- [ ] Implement and persist the recovery transition.
- [ ] Run focused and full tests.

### Task 4: Dependencies, scripts, and documentation

**Files:**
- Modify: `requirements.txt`
- Modify: `监测20分钟.bat`
- Modify: `README.md`
- Modify: `tests/test_project_files.py`

**Interfaces:**
- Produces: reproducible dependency and launcher declarations.

- [ ] Write failing file-contract tests for `openpyxl` and portable Python selection.
- [ ] Verify they fail.
- [ ] Update dependency, batch launcher, and runtime documentation.
- [ ] Run the full suite plus Python and Node syntax checks.
