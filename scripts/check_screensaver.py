#!/usr/bin/env python3
"""Check launcher safeguards and non-destructive idle/menu integration."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import install_screensaver as installer


class ScreensaverChecks(unittest.TestCase):
    def test_idle_patch_preserves_controller(self):
        source = '  function launchScreensaver() {\n    run("omarchy-launch-screensaver")\n  }\n'
        patched = installer.patch_service(source)
        self.assertEqual(installer.patch_service(patched), patched)
        restored = patched.replace("  " + installer.MARKER + "\n", "").replace(
            installer.LAUNCHER, "omarchy-launch-screensaver")
        self.assertEqual(restored, source)
        with self.assertRaises(ValueError):
            installer.patch_service("unknown future idle service")

    def test_menu_preserves_existing_entries_and_is_repeatable(self):
        raw = '{\n// User comment\n"personal.notes":{"action":"editor notes"},\n}'
        menu = installer.update_menu(raw)
        self.assertEqual(menu["personal.notes"]["action"], "editor notes")
        self.assertEqual(installer.update_menu(json.dumps(menu)), menu)
        wrapped = installer.update_menu('{"items":{"personal": {"label":"Personal"}}}')
        self.assertIn("personal", wrapped["items"])
        self.assertIn("elvis-screensaver.enabled", wrapped["items"])

    def test_launcher_guards_force_and_toggle(self):
        with tempfile.TemporaryDirectory(prefix="elvis-screensaver-check-") as temporary:
            base = Path(temporary)
            bin_dir = base / "bin"
            bin_dir.mkdir()
            config = base / ".config/omarchy/elvis-screensaver"
            config.mkdir(parents=True)
            (config / "photos.json").write_text('{"photos":[]}')
            mock = '''#!/bin/bash
case "${0##*/}" in
  omarchy-toggle-enabled) test -f "$HOME/off" ;;
  omarchy-toggle) if test -f "$HOME/off"; then rm "$HOME/off"; else touch "$HOME/off"; fi ;;
  omarchy-shell) echo "${TEST_LOCKED:-false}" ;;
  quickshell) printf '%s\\n' "$*" >>"$HOME/calls" ;;
  omarchy-notification-send) : ;;
esac
'''
            for name in ["omarchy-toggle-enabled", "omarchy-toggle", "omarchy-shell",
                         "quickshell", "omarchy-notification-send"]:
                path = bin_dir / name
                path.write_text(mock)
                path.chmod(0o755)
            environment = dict(os.environ, HOME=str(base), PATH=f"{bin_dir}:/usr/bin")
            launcher = installer.ROOT / "scripts/elvis-screensaver"

            def launch(*args, locked="false"):
                subprocess.run(["bash", str(launcher), *args], check=True,
                               env=dict(environment, TEST_LOCKED=locked))

            calls = base / "calls"
            launch(locked="true")
            launch(locked="unavailable")
            self.assertFalse(calls.exists(), "A locked or unavailable lock service must refuse launch")
            (base / "off").touch()
            launch()
            self.assertFalse(calls.exists(), "The normal launch must respect the off switch")
            launch("--force")
            self.assertIn("--no-duplicate", calls.read_text())
            calls.unlink()
            launch("--force", locked="true")
            self.assertFalse(calls.exists(), "Force preview must not bypass the lock guard")
            launch("--toggle")
            self.assertFalse((base / "off").exists())
            launch("--toggle")
            self.assertTrue((base / "off").exists())
            self.assertIn("call screensaver stop", calls.read_text())


if __name__ == "__main__":
    unittest.main()
