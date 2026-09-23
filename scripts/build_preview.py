#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
template = (root / 'preview/template.html').read_text()
data = (root / 'assets/portraits.json').read_text().strip()
(root / 'preview/index.html').write_text(template.replace('__PORTRAITS__', data))
print(root / 'preview/index.html')
