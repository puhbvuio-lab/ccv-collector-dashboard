# Editable CCV Excel Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the existing dashboard Excel download with complete sampling attributes and native editable CCV charts.

**Architecture:** Keep the existing `TaskManager.export_xlsx(task_id)` endpoint and build the workbook with `openpyxl`. Read each stream's complete CSV, enrich rows from stream summary metadata, write a normalized sample sheet, then create one native line-chart series per stream session from workbook cell references.

**Tech Stack:** Python 3, `openpyxl`, `unittest`, CSV

**Spec:** `docs/superpowers/specs/2026-10-30-editable-xlsx-export-design.md`

## Global Constraints

- Preserve the existing `/api/tasks/<id>/export.xlsx` route and dashboard button.
- The primary sheet columns are sampling time (UTC+8), livestream link, streamer name, livestream title, CCV, and stream session ID.
- Livestream links must be clickable absolute Twitch HTTPS links.
- Charts must be native Excel line charts, not embedded PNG images.
- Prefer complete stream CSV data and tolerate missing legacy metadata.

## Review Focus

- A title that changes during one stream must remain correct on each sample row; Task 1 tests two distinct titles.
- A display name missing from legacy summary data must fall back to channel login; Task 1 tests this fallback.
- Timestamps containing `Z`, explicit offsets, or malformed legacy text must not abort export; Task 1 tests valid offset conversion and malformed fallback.
- Stream CSV formula-like text must remain text and never become an Excel formula; Task 1 tests a title beginning with `=`.
- An export with summary metadata but no usable samples must remain a valid workbook with no empty chart; Task 2 tests this condition.

---

### Task 1: Complete Sampling Data Sheet

**Files:**
- Modify: `server.py:559-598`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `TaskManager.task_dir(task_id)`, `TaskManager.list_streams(task_id)` and stream CSV files named `<channel>_<stream_id>.csv`.
- Produces: `TaskManager.export_xlsx(task_id) -> bytes` with a `采样数据` sheet containing Excel datetime values, hyperlinks, display names, per-sample titles, numeric CCV values and stream IDs.

- [ ] **Step 1: Write failing export-data tests**

Add `ExcelExportTests` fixtures using a temporary task directory and assert literal headers, UTC+8 datetime conversion, `https://www.twitch.tv/tenz` hyperlink, display-name fallback, two per-sample titles, numeric CCV values, formula-like title stored as text, and stream ID.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_server.ExcelExportTests -v`

Expected: FAIL because the current workbook only has `汇总` and `CCV时序` with four columns.

- [ ] **Step 3: Implement normalized sample export**

In `server.py`, add narrowly scoped timestamp and Excel-safe text helpers near `TaskManager.export_xlsx`, and update `export_xlsx(task_id) -> bytes` to populate `采样数据` from full stream CSV rows with metadata fallbacks and hyperlink styling.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests.test_server.ExcelExportTests -v`

Expected: sampling-data tests PASS.

### Task 2: Native Editable Trend Charts

**Files:**
- Modify: `server.py:559-598`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: row ranges written to `采样数据` by Task 1.
- Produces: a `CCV趋势图` sheet whose `openpyxl.chart.LineChart` objects contain one editable series per non-empty stream session and reference time/CCV cells in `采样数据`.

- [ ] **Step 1: Write failing chart tests**

Assert that a workbook with two stream sessions has a `CCV趋势图` sheet, one line chart with two series, time-axis and CCV-axis titles, series formulas that reference the sample sheet, and no chart when the summaries have no usable sample rows.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_server.ExcelExportTests -v`

Expected: FAIL because the current export creates no native charts.

- [ ] **Step 3: Implement native chart construction**

Create a `LineChart` on `CCV趋势图`, add each stream session as a series using `Reference` ranges over its contiguous sample rows, apply the literal series name `<display_name> · <stream_id>`, set time and CCV axis titles, and skip chart creation when no series has data.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests.test_server.ExcelExportTests -v`

Expected: all Excel export tests PASS.

### Task 3: Regression and Artifact Verification

**Files:**
- Modify: `README.md`
- Test: existing `tests/`

**Interfaces:**
- Consumes: final workbook bytes from Tasks 1-2.
- Produces: documented export behavior and verification evidence.

- [ ] **Step 1: Document the enhanced export**

Update the dashboard export section in `README.md` with the two sheet names, core attributes, Beijing-time convention and editable native-chart behavior.

- [ ] **Step 2: Run the full automated suite**

Run: `python -m unittest discover -s tests -t . -v`

Expected: all tests PASS.

- [ ] **Step 3: Run workbook and syntax verification**

Load generated bytes with `openpyxl`, verify sheet names and chart count, run Python AST checks, and run `git diff --check -- . ':(exclude)server.py'` (the existing `server.py` CRCRLF format produces false-positive whitespace reports).

- [ ] **Step 4: Review the final diff**

Confirm no route or dashboard-button changes, no static-image chart path, and no unrelated user changes were overwritten.
