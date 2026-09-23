#!/usr/bin/env python3
"""Install the photo screensaver and change only the cloned idle launcher."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ORIGINALS = [
    "772725955_2315786472590446_335888140933700927_n.jpg",
    "703861528_17997792578956004_3653670580096013406_n.jpeg",
    "775020719_18010620785956004_8913760364555554077_n.jpeg",
]
MARKER = "// Elvis photo screensaver launcher; idle and lock logic stays with Omarchy."
LAUNCHER = r'exec \"$HOME/.local/bin/elvis-screensaver\"'
MENU_ENTRIES = {
    "elvis-screensaver": {"icon": "󱄄", "label": "Elvis Screensaver", "aliases": ["elvis"],
                          "description": "Original Elvis photos, preview, and on/off switch"},
    "elvis-screensaver.preview": {"icon": "", "label": "Preview",
                                  "action": '\"$HOME/.local/bin/elvis-screensaver\" --force',
                                  "description": "Show now, even with Stay Awake on. Move the mouse or press a key to close."},
    "elvis-screensaver.enabled": {"icon": "󱄄", "label": "Enabled",
                                  "action": '\"$HOME/.local/bin/elvis-screensaver\" --toggle',
                                  "checked": "! omarchy-toggle-enabled screensaver-off",
                                  "description": "Toggle photo playback on or off. Does not change automatic locking."},
    "system.screensaver": {"icon": "󱄄", "label": "Elvis Screensaver",
                           "action": '\"$HOME/.local/bin/elvis-screensaver\" --force'},
    "trigger.toggle.screensaver": {"icon": "󱄄", "label": "Elvis Screensaver",
                                    "action": '\"$HOME/.local/bin/elvis-screensaver\" --toggle',
                                    "checked": "! omarchy-toggle-enabled screensaver-off"},
}


def update_menu(raw):
    # Match the JSONC syntax supported by Omarchy's MenuModel.js.
    stripped = re.sub(r"^\s*//[^\n]*(\n|$)", "", raw, flags=re.MULTILINE)
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    menu = json.loads(stripped) if stripped.strip() else {}
    if not isinstance(menu, dict):
        raise ValueError("Menu extensions must be a JSON object")
    entries = menu.get("items", menu)
    if not isinstance(entries, dict):
        raise ValueError("Menu items must be a JSON object")
    entries.update(MENU_ENTRIES)
    return menu


def patch_service(source):
    if MARKER in source and LAUNCHER in source:
        return source
    if source.count("omarchy-launch-screensaver") != 1:
        raise ValueError("This idle plugin has an unfamiliar launcher. Nothing was replaced.")
    return source.replace("  function launchScreensaver() {",
                          f"  {MARKER}\n  function launchScreensaver() {{").replace(
                              "omarchy-launch-screensaver", LAUNCHER)


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()


def write_json(path, data):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photos", nargs="*", type=Path, help="Photos in playback order")
    parser.add_argument("--photos-dir", type=Path, help="Directory containing the three original Elvis photos")
    args = parser.parse_args()
    if args.photos and args.photos_dir:
        parser.error("Use photo paths or --photos-dir, not both")
    photos = [args.photos_dir / name for name in ORIGINALS] if args.photos_dir else args.photos
    photos = [path.expanduser().resolve(strict=True) for path in photos]
    if any(not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}
           for path in photos):
        parser.error("Photos must be readable JPEG, PNG, or WebP files")

    home = Path.home()
    config = home / ".config/omarchy"
    destination = config / "elvis-screensaver"
    menu_path = config / "extensions/omarchy-menu.jsonc"
    menu = update_menu(menu_path.read_text() if menu_path.exists() else "{}")
    settings_path = destination / "photos.json"
    if not photos and not settings_path.exists():
        parser.error("Supply photos for the first installation")
    plugin_id = f"{getpass.getuser()}.idle"
    clone = config / "plugins" / plugin_id
    catalog = json.loads(run("omarchy", "plugin", "list", "--json"))
    # Do not take over a different customized idle service.
    if clone.exists():
        manifest_path = clone / "manifest.json"
        if not manifest_path.exists() or not json.loads(manifest_path.read_text()).get("elvisScreensaver"):
            raise SystemExit(f"{clone} already exists and is not managed by this installer.")
    elif any(entry.get("id") == "omarchy.idle" and not entry.get("enabled") for entry in catalog):
        raise SystemExit("The built-in idle service is already disabled. Refusing to replace another idle setup.")

    source = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "shell/plugins/services/idle/Service.qml"
    patch_service(source.read_text())  # Validate compatibility before installing or enabling anything.
    run("omarchy", "shell", "shell", "ping")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = config / "backups/elvis-screensaver" / stamp
    backup.mkdir(parents=True)
    shutil.copy2(config / "shell.json", backup / "shell.json")
    if menu_path.exists():
        shutil.copy2(menu_path, backup / "omarchy-menu.jsonc")
    for path in [destination, clone, home / ".local/bin/elvis-screensaver"]:
        if path.is_dir():
            shutil.copytree(path, backup / path.name)
        elif path.is_file():
            shutil.copy2(path, backup / "elvis-screensaver-launcher")

    destination.mkdir(parents=True, exist_ok=True)
    for name in ["Slideshow.qml", "org.omarchy.screensaver.qml"]:
        shutil.copy2(ROOT / "screensaver" / name, destination / name)
    launcher = home / ".local/bin/elvis-screensaver"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scripts/elvis-screensaver", launcher)
    launcher.chmod(0o755)
    if photos:
        # Copies live only in personal configuration, never inside the Git repository.
        photo_dir = destination / "photos"
        photo_dir.mkdir(exist_ok=True)
        installed = []
        for index, photo in enumerate(photos):
            target = photo_dir / f"{index:03d}{photo.suffix.lower()}"
            if photo != target:
                shutil.copy2(photo, target)
            installed.append(target.as_uri())
        settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
        settings["photos"] = installed
        settings.setdefault("intervalMs", 8000)
        write_json(settings_path, settings)

    if not clone.exists():
        print(run("omarchy", "plugin", "clone", "omarchy.idle"))
    service = clone / "Service.qml"
    patched = patch_service(service.read_text())
    temporary = clone / "Service.qml.tmp"
    temporary.write_text(patched)
    temporary.replace(service)
    manifest = json.loads((clone / "manifest.json").read_text())
    manifest.update(name="Elvis Idle", description="Omarchy idle and lock timers with the Elvis photo screensaver.",
                    elvisScreensaver=True)
    write_json(clone / "manifest.json", manifest)
    run("omarchy", "plugin", "validate", str(clone))
    run("omarchy", "shell", "shell", "rescanPlugins")
    print(run("omarchy", "plugin", "enable", plugin_id))
    menu_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(menu_path, menu)
    print(f"Installed Elvis screensaver. Backup: {backup}")
    print("Run: omarchy restart shell")
    print(f"Preview: {launcher} --force")
    print("Menu: Omarchy > Elvis Screensaver > Preview / Enabled")
    print("Your existing idle timings and Stay Awake setting were preserved.")


if __name__ == "__main__":
    main()
