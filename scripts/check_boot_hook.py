#!/usr/bin/env python3
"""Check once-per-session hook behavior without touching the live session."""
import os
import subprocess
import tempfile
from pathlib import Path

hook = Path(__file__).resolve().with_name('elvis-tcb-boot')
with tempfile.TemporaryDirectory(prefix='elvis-tcb-hook-') as directory:
    root = Path(directory)
    binary = root/'bin'
    binary.mkdir()
    mock = binary/'omarchy'
    mock.write_text('#!/bin/bash\nprintf "checking\\n"\n')
    mock.chmod(0o755)
    env = {**os.environ, 'XDG_RUNTIME_DIR': str(root), 'HYPRLAND_INSTANCE_SIGNATURE': 'session-one',
           'PATH': str(binary)+os.pathsep+os.environ['PATH']}
    subprocess.run(['bash', str(hook)], env=env, check=True)
    marker = root/'elvis-tcb-boot/session-one.state'
    assert marker.read_text() == 'pending\n'
    subprocess.run(['bash', str(hook)], env=env, check=True)
    assert marker.read_text() == 'pending\n'
    marker.write_text('played\n')
    subprocess.run(['bash', str(hook)], env=env, check=True)
    assert marker.read_text() == 'played\n', 'Repeated startup hook reset consumption'
    env['HYPRLAND_INSTANCE_SIGNATURE'] = 'session-two'
    subprocess.run(['bash', str(hook)], env=env, check=True)
    assert (root/'elvis-tcb-boot/session-two.state').read_text() == 'pending\n'
    assert marker.read_text() == 'played\n'
    print('PASS startup request creation, idempotence, consumption preservation, and new-session eligibility')
