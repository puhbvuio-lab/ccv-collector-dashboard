import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class YoutubeRemovalTests(unittest.TestCase):
    def test_repository_has_no_builtin_youtube_collector_surface(self):
        self.assertFalse((ROOT / "yt_web_pilot.js").exists())
        self.assertFalse((ROOT / "docs" / "ccv-monitor-workflow.drawio").exists())
        self.assertFalse((ROOT / "docs" / "ccv-monitor-workflow.drawio.png").exists())
        self.assertFalse((ROOT / "examples" / "yt_7RWSqGjsSNc_网页观众数_10min.png").exists())
        self.assertFalse((ROOT / "examples" / "yt_7RWSqGjsSNc_网页实时CCV_数据图表_20260806_185943.xlsx").exists())

        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
        package = (ROOT / "package.json").read_text(encoding="utf-8")
        server_source = (ROOT / "server.py").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("YOUTUBE_API_KEY", env_example)
        self.assertNotIn("Twitch/YouTube", package)
        for forbidden in (
            "YoutubeMonitor",
            "googleapis.com/youtube",
            "youtube.com/oembed",
            "yt_web_pilot",
            "parse_youtube_target",
            "YOUTUBE_API_KEY",
        ):
            self.assertNotIn(forbidden, server_source)
        for forbidden in ("YouTube Data API", 'platform = "youtube"', "yt_web_pilot.js"):
            self.assertNotIn(forbidden, readme)


if __name__ == "__main__":
    unittest.main()
