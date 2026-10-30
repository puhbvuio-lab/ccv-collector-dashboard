import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallationContractTests(unittest.TestCase):
    def test_requirements_install_builtin_xlsx_export_dependency(self):
        requirements = {
            line.split("=", 1)[0].split(">", 1)[0].strip().lower()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertIn("openpyxl", requirements)


class LauncherContractTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows batch launcher")
    def test_twenty_minute_launcher_uses_python_from_current_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy2(ROOT / "监测20分钟.bat", root / "监测20分钟.bat")
            (root / "python.cmd").write_text(
                "@echo off\r\necho %* > invoked.txt\r\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PATH"] = f"{root}{os.pathsep}{env.get('PATH', '')}"

            subprocess.run(
                ["cmd.exe", "/c", str(root / "监测20分钟.bat")],
                cwd=root,
                env=env,
                input="\n",
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )

            self.assertTrue((root / "invoked.txt").exists(), "launcher did not invoke PATH python")
            invocation = (root / "invoked.txt").read_text(encoding="utf-8").strip()
            self.assertEqual("monitor.py --duration 20 --auto-charts", invocation)
