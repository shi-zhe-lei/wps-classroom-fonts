#!/usr/bin/env python3
"""Build only committed, audited public files. Ignored fonts never enter the ZIP."""
import hashlib
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run(['git', '-C', str(root), 'diff', '--quiet', 'HEAD'], check=True)
subprocess.run([sys.executable, str(root / 'tools/verify-public.py'), '--ref', 'HEAD'], check=True)
version = subprocess.check_output(['git', '-C', str(root), 'show', 'HEAD:VERSION'], text=True).strip()
if not version or any(c not in '0123456789.-' for c in version):
    raise ValueError('Invalid version')
output = root / 'build' / f'wps-classroom-fonts-v{version}.zip'
output.parent.mkdir(exist_ok=True)
subprocess.run(['git', '-C', str(root), 'archive', '--format=zip', '--prefix=wps-classroom-fonts/', f'--output={output}', 'HEAD'], check=True)
digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
print(f'Created build/{output.name} ({output.stat().st_size / 1024 / 1024:.2f} MiB)')
