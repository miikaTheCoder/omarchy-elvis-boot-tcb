#!/usr/bin/env python3
"""Render the QML scene at exact pixel dimensions, independent of the window.

Start `quickshell -p ./preview.qml` first. Frames are laid out natively at the
requested resolution, not upscaled from a screenshot. Temporary PNGs are
validated and deleted after encoding; a lossless settled still is also saved.
"""
import argparse
import math
import struct
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ['quickshell', 'ipc', '-p', str(ROOT/'preview.qml'), 'call', 'preview']


def ipc(*args):
    return subprocess.check_output(PREFIX + [str(arg) for arg in args], text=True).strip()


def capture(time_ms, destination, size):
    destination.unlink(missing_ok=True)
    ipc('exportFrame', time_ms, destination)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if destination.exists():
            data = destination.read_bytes()
            if len(data) >= 32 and data[-12:] == b'\x00\x00\x00\x00IEND\xaeB`\x82':
                dimensions = struct.unpack('>II', data[16:24])
                if dimensions != size:
                    raise RuntimeError(f'Expected native {size} render, received {dimensions}')
                return
        time.sleep(.015)
    raise RuntimeError(f'Preview did not finish saving {destination}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tcb', action='store_true')
    parser.add_argument('--width', type=int, default=1920)
    parser.add_argument('--height', type=int, default=1080)
    parser.add_argument('--fps', type=int, default=60)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not (320 <= args.width <= 7680 and 240 <= args.height <= 4320):
        parser.error('Dimensions must be between 320×240 and 7680×4320')
    if args.width % 2 or args.height % 2 or not 1 <= args.fps <= 120:
        parser.error('Use even dimensions and a frame rate from 1 to 120')
    output = args.output or ROOT/('preview/tcb-boot.mp4' if args.tcb else 'preview/elvis-sequence.mp4')
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = 2500 if args.tcb else 3500
    if ipc('exportSize', args.width, args.height) != 'ok':
        raise RuntimeError('Preview lacks export support; restart it using the current preview.qml')
    ipc('mode', 'tcb' if args.tcb else 'portraits')
    with tempfile.TemporaryDirectory(prefix='elvis-render-') as directory:
        frames = Path(directory)
        for index in range(math.ceil(duration * args.fps / 1000)):
            capture(index * 1000 / args.fps, frames/f'{index:04}.png', (args.width, args.height))
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(args.fps),
            '-i', str(frames/'%04d.png'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)
        ], check=True)
    capture(1400 if args.tcb else 800, output.with_suffix('.png'), (args.width, args.height))
    ipc('frame', 1400 if args.tcb else 800)
    print(f'{output} ({args.width}×{args.height}, {args.fps} fps)')
    print(f'Lossless still: {output.with_suffix(".png")}')


if __name__ == '__main__':
    main()
