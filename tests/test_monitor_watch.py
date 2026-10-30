import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import monitor


def state_machine(cfg=None):
    instance = monitor.Monitor.__new__(monitor.Monitor)
    instance.cfg = cfg or {
        "channels": ["tenz"],
        "watch_interval_seconds": 30,
        "live_interval_seconds": 45,
        "poll_interval_seconds": 45,
    }
    instance._phase = "waiting"
    instance._offline_streak = 0
    instance.last_live_count = 0
    instance.state = {"streams": {}}
    return instance


class ChannelWatchStateTests(unittest.TestCase):
    def test_waiting_and_live_phases_use_independent_intervals(self):
        watcher = state_machine()
        self.assertEqual("waiting", watcher.current_phase())
        self.assertEqual(30, watcher.current_interval_seconds())

        watcher.record_channel_observation(1)

        self.assertEqual("live", watcher.current_phase())
        self.assertEqual(45, watcher.current_interval_seconds())

    def test_two_empty_observations_confirm_offline_and_return_to_waiting(self):
        watcher = state_machine()
        watcher.record_channel_observation(1)

        first = watcher.record_channel_observation(0)
        self.assertFalse(first)
        self.assertEqual("live", watcher.current_phase())

        second = watcher.record_channel_observation(0)
        self.assertTrue(second)
        self.assertEqual("waiting", watcher.current_phase())
        self.assertEqual(30, watcher.current_interval_seconds())

    def test_new_live_observation_after_waiting_returns_to_live(self):
        watcher = state_machine()
        watcher.record_channel_observation(1)
        watcher.record_channel_observation(0)
        watcher.record_channel_observation(0)

        watcher.record_channel_observation(1)

        self.assertEqual("live", watcher.current_phase())
        self.assertEqual(0, watcher._offline_streak)

    def test_duration_limit_does_not_apply_to_channel_watch(self):
        channel = state_machine({"channels": ["tenz"]})
        game = state_machine({"channels": []})
        self.assertFalse(channel.duration_limit_applies())
        self.assertTrue(game.duration_limit_applies())


class HeartbeatTests(unittest.TestCase):
    def test_waiting_heartbeat_exposes_phase_and_both_intervals(self):
        with tempfile.TemporaryDirectory() as tmp:
            watcher = state_machine()
            watcher.data_dir = Path(tmp)
            watcher.session_id = "session"
            watcher.session_started_at = datetime(2026, 10, 30, tzinfo=timezone.utc)

            watcher.write_heartbeat(datetime(2026, 10, 30, 0, 1, tzinfo=timezone.utc), 0)

            heartbeat = json.loads((Path(tmp) / "heartbeat.json").read_text(encoding="utf-8"))
            self.assertEqual("waiting", heartbeat["phase"])
            self.assertEqual(30, heartbeat["watch_interval_seconds"])
            self.assertEqual(45, heartbeat["live_interval_seconds"])
            self.assertEqual(30, heartbeat["next_interval_seconds"])


class FailingChannelClient:
    def get(self, path, params):
        raise RuntimeError("temporary Twitch API failure")

    def resolve_game_id(self, *args, **kwargs):
        raise AssertionError("channel watch must not resolve a game")

    def get_live_streams(self, *args, **kwargs):
        raise AssertionError("channel watch must not query a game category")


class ChannelQueryFailureTests(unittest.TestCase):
    def test_repeated_api_errors_do_not_confirm_stream_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {
                "data_dir": str(root / "data"),
                "charts_dir": str(root / "charts"),
                "channels": ["tenz"],
                "languages": [],
                "max_streams": 1,
                "watch_interval_seconds": 30,
                "live_interval_seconds": 30,
                "poll_interval_seconds": 30,
                "monitor_duration_minutes": 0,
            }
            watcher = monitor.Monitor(cfg, FailingChannelClient())
            watcher._phase = "live"
            watcher.state["streams"]["stream-1"] = {
                "stream_id": "stream-1",
                "channel": "tenz",
                "first_seen_utc": "2026-10-30T00:00:00+00:00",
                "last_seen_utc": "2026-10-30T00:01:00+00:00",
                "status": "live",
                "samples": [],
            }

            with self.assertLogs(level="WARNING"):
                watcher.tick()
                watcher.tick()

            self.assertEqual("live", watcher.state["streams"]["stream-1"]["status"])
            self.assertEqual("live", watcher.current_phase())
            self.assertEqual(0, watcher._offline_streak)


if __name__ == "__main__":
    unittest.main()
