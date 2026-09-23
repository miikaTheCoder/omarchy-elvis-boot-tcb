#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
plugin_id=nextg.elvis-unlock
target_dir="$HOME/.config/omarchy/plugins/$plugin_id"
stamp="$(date +%Y%m%d-%H%M%S)"

omarchy plugin validate "$project_dir/plugin/$plugin_id"
omarchy shell shell ping >/dev/null
mkdir -p "$HOME/.config/omarchy/backups/elvis-unlock/$stamp"
cp -a "$HOME/.config/omarchy/shell.json" "$HOME/.config/omarchy/backups/elvis-unlock/$stamp/shell.json"
if [[ -e "$target_dir" ]]; then
    cp -a "$target_dir" "$HOME/.config/omarchy/backups/elvis-unlock/$stamp/$plugin_id"
fi
boot_hook="$HOME/.config/omarchy/hooks/post-boot.d/elvis-tcb-boot"
if [[ -f "$boot_hook" ]]; then
    cp -a "$boot_hook" "$HOME/.config/omarchy/backups/elvis-unlock/$stamp/elvis-tcb-boot"
fi
mkdir -p "$target_dir"
cp "$project_dir/plugin/$plugin_id/"{manifest.json,Service.qml,Sequence.qml,Portrait.qml,Portraits.js,TcbArt.js,TcbMark.qml,BootSequence.qml} "$target_dir/"
omarchy hook install post-boot "$project_dir/scripts/elvis-tcb-boot"
omarchy shell shell rescanPlugins >/dev/null
omarchy plugin enable "$plugin_id"
status="$(omarchy shell elvis status)"
printf '%s\n' "$status"
if ! jq -e 'has("bootConsumed")' <<<"$status" >/dev/null 2>&1; then
    echo "Installed. The shell still has the previous QML code cached; run: omarchy restart shell"
fi
