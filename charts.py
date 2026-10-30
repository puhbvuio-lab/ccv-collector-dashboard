#!/usr/bin/env python3
"""从采集数据生成图表。

对每个任务目录 data/<task_id>/ 生成:
  charts/<task_id>/<channel>_<stream_id>.png   每场直播 CCV 曲线
  charts/<task_id>/overview_<时间>.png         该任务全部直播 CCV 曲线对比（按开播后分钟对齐）
  charts/<task_id>/summary_<时间>.png          该任务各主播峰值 CCV 柱状图

用法:
  python charts.py                                          # 扫描全部任务目录出图
  python charts.py --data-dir data/<task_id> --out-dir charts/<task_id>
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# Windows 中文字体（微软雅黑），保证图里中文不乱码
for font_candidate in [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\simhei.ttf",
]:
    if Path(font_candidate).exists():
        fm.fontManager.addfont(font_candidate)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "Malgun Gothic", "SimHei", "Arial"]
plt.rcParams["axes.unicode_minus"] = False


def safe_title(value: str) -> str:
    """保留中/日/英/数字/常见符号，其余字符（韩文、emoji 等）替换为 ?，避免字体缺字形。"""
    out = []
    for ch in str(value or ""):
        code = ord(ch)
        if (
            0x20 <= code <= 0x7E
            or 0x4E00 <= code <= 0x9FFF
            or 0x3000 <= code <= 0x303F
            or 0xFF00 <= code <= 0xFFEF
            or 0x3040 <= code <= 0x30FF
            or 0x3400 <= code <= 0x4DBF
        ):
            out.append(ch)
        else:
            out.append("?")
    return "".join(out)


def load_config() -> dict:
    cfg_path = BASE_DIR / "config.json"
    return json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}


def local_tz(cfg: dict) -> ZoneInfo:
    return ZoneInfo(cfg.get("timezone", "Asia/Singapore"))


def read_stream_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["viewer_count"] = pd.to_numeric(df["viewer_count"], errors="coerce")
    return df.dropna(subset=["viewer_count"])


def read_summary(data_dir: Path) -> pd.DataFrame:
    summary = data_dir / "streams_summary.csv"
    if not summary.exists():
        return pd.DataFrame()
    return pd.read_csv(summary, encoding="utf-8-sig")


def plot_stream(df: pd.DataFrame, meta: dict, out_dir: Path, tz: ZoneInfo) -> None:
    local = df["ts_utc"].dt.tz_convert(tz)
    viewers = df["viewer_count"]
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    ax.plot(local, viewers, linewidth=1.4, color="#1f77b4")
    ax.fill_between(local, viewers, color="#1f77b4", alpha=0.15)
    ax.set_title(
        f"{safe_title(meta.get('display_name', meta.get('channel', '')))}  CCV 实时变化\n"
        f"峰值 {int(viewers.max())} / 均值 {int(viewers.mean())} / 采样 {len(viewers)} 次",
        fontsize=12,
    )
    ax.set_ylabel("CCV（同时在线观看人数）")
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M", tz=tz))
    fig.autofmt_xdate()
    fig.tight_layout()
    out = out_dir / f"{meta.get('channel', '')}_{meta.get('stream_id', '')}.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_overview(streams: list[tuple[pd.DataFrame, dict]], out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(13, 7), dpi=150)

    def peak_key(item: tuple[pd.DataFrame, dict]) -> float:
        df, meta = item
        value = pd.to_numeric(meta.get("peak_ccv"), errors="coerce")
        if pd.isna(value):
            value = float(df["viewer_count"].max())
        return float(value) if pd.notna(value) else 0.0

    streams_sorted = sorted(
        streams,
        key=peak_key,
        reverse=True,
    )
    legend_limit = 15
    for index, (df, meta) in enumerate(streams_sorted):
        minutes = (df["ts_utc"] - df["ts_utc"].iloc[0]).dt.total_seconds() / 60.0
        label = f"{meta.get('channel')} (峰值 {int(df['viewer_count'].max())})"
        ax.plot(minutes, df["viewer_count"], linewidth=1.3, label=label if index < legend_limit else None)
    extra = len(streams_sorted) - legend_limit
    title = "直播 CCV 对比（按开播后分钟对齐）"
    if extra > 0:
        title += f"（图例仅显示峰值前 {legend_limit} 场，其余 {extra} 场略）"
    ax.set_title(title, fontsize=13)
    ax.set_xlabel("开播后分钟数")
    ax.set_ylabel("CCV")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    fig.tight_layout()
    out = out_dir / f"overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_summary(summary: pd.DataFrame, out_dir: Path) -> Path:
    summary = summary.copy()
    summary["peak_ccv"] = pd.to_numeric(summary["peak_ccv"], errors="coerce").fillna(0)
    summary = summary.sort_values("peak_ccv", ascending=False)
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)
    colors = ["#d62728" if s == "live" else "#1f77b4" for s in summary["status"]]
    bars = ax.bar(summary["channel"], summary["peak_ccv"], color=colors)
    for bar, value in zip(bars, summary["peak_ccv"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(int(value)), ha="center", va="bottom", fontsize=8)
    ax.set_title("各主播直播峰值 CCV（红=直播中，蓝=已结束）", fontsize=13)
    ax.set_ylabel("峰值 CCV")
    ax.grid(axis="y", alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    out = out_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def build_charts(data_dir: Path, out_dir: Path, tz: ZoneInfo) -> int:
    """为单个任务数据目录生成图表，返回生成场次图的数量。"""
    streams_dir = data_dir / "streams"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not streams_dir.exists():
        return 0

    summary = read_summary(data_dir)
    meta_map: dict[str, dict] = {}
    if not summary.empty:
        for _, row in summary.iterrows():
            meta_map[str(row["stream_id"])] = dict(row)

    streams: list[tuple[pd.DataFrame, dict]] = []
    for csv_path in sorted(streams_dir.glob("*.csv")):
        df = read_stream_csv(csv_path)
        if df.empty:
            continue
        stream_id = csv_path.stem.split("_", 1)[1] if "_" in csv_path.stem else csv_path.stem
        meta = meta_map.get(stream_id, {"channel": csv_path.stem, "stream_id": stream_id})
        meta.setdefault("channel", csv_path.stem)
        meta.setdefault("stream_id", stream_id)
        plot_stream(df, meta, out_dir, tz)
        streams.append((df, meta))

    if not streams:
        return 0

    plot_overview(streams, out_dir)
    if not summary.empty:
        plot_summary(summary, out_dir)
    return len(streams)


def main() -> None:
    parser = argparse.ArgumentParser(description="从采集数据生成 CCV 趋势图表")
    parser.add_argument("--data-dir", default=None, help="指定任务数据目录（如 data/twitch_zrush_165300），默认扫描全部任务")
    parser.add_argument("--out-dir", default=None, help="图表输出目录，默认 charts/<任务ID>/")
    args = parser.parse_args()

    cfg = load_config()
    tz = local_tz(cfg)
    base = BASE_DIR / cfg.get("data_dir", "data")
    charts_root = BASE_DIR / cfg.get("charts_dir", "charts")

    if args.data_dir:
        data_dirs = [Path(args.data_dir)]
    else:
        data_dirs = sorted(
            [d for d in base.iterdir() if d.is_dir() and (d / "streams_summary.csv").exists()]
        )

    if not data_dirs:
        print("没有找到采集数据。请先运行采集，或指定 --data-dir")
        return

    total = 0
    for data_dir in data_dirs:
        out_dir = Path(args.out_dir) if args.out_dir else (charts_root / data_dir.name)
        n = build_charts(data_dir, out_dir, tz)
        if n:
            print(f"[{data_dir.name}] 单场图 {n} 张 -> {out_dir}")
            total += n
        else:
            print(f"[{data_dir.name}] 无可用时序数据，跳过")

    print(f"完成：共 {len(data_dirs)} 个任务目录，{total} 场直播出图")


if __name__ == "__main__":
    main()
