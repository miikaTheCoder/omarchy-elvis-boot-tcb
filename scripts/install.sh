#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
plugin_id=nextg.elvis-unlock
target_dir="$HOME/.config/omarchy/plugins/$plugin_id"
expected_version="$(jq -r '.version' "$project_dir/plugin/$plugin_id/manifest.json")"
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

# Plugin discovery runs asynchronously. Wait until the shell has indexed this
# service before enabling it; otherwise enablePlugin can answer "unknown" and
# leave the `elvis` IPC target unloaded even though all files were installed.
plugin_discovered=false
for _ in {1..50}; do
    catalog="$(omarchy shell shell listPlugins 2>/dev/null || true)"
    if jq -e --arg id "$plugin_id" 'any(.[]; .id == $id)' <<<"$catalog" >/dev/null 2>&1; then
        plugin_discovered=true
        break
    fi
    sleep 0.1
done
if [[ "$plugin_discovered" != true ]]; then
    echo "Installation copied the plugin, but Omarchy did not discover it. Run: omarchy restart shell" >&2
    exit 1
fi

omarchy plugin enable "$plugin_id"
status="$(omarchy shell elvis status 2>/dev/null || true)"
if ! jq -e --arg version "$expected_version" '.version == $version' <<<"$status" >/dev/null 2>&1; then
    echo "Restarting the shell to load Elvis TCB $expected_version..."
    omarchy restart shell
    for _ in {1..100}; do
        status="$(omarchy shell elvis status 2>/dev/null || true)"
        if jq -e --arg version "$expected_version" '.version == $version' <<<"$status" >/dev/null 2>&1; then
            break
        fi
        sleep 0.1
    done
fi
printf '%s\n' "$status"
jq -e --arg version "$expected_version" '.version == $version' <<<"$status" >/dev/null 2>&1 || {
    echo "Installed the files, but Elvis TCB $expected_version did not load." >&2
    exit 1
}
