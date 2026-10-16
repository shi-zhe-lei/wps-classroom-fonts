#!/usr/bin/env python3
"""Audit exact Git objects, never the ignored working-directory font copies."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    parser = argparse.ArgumentParser(description='检查暂存区或指定提交中的公开文件。')
    parser.add_argument('--ref', help='例如 HEAD；默认检查暂存区')
    args = parser.parse_args()
    items = []
    if args.ref:
        for record in git('ls-tree', '-rz', args.ref).split(b'\0'):
            if record:
                meta, name = record.split(b'\t', 1)
                mode, kind, oid = meta.decode().split()
                if kind != 'blob':
                    raise ValueError('Submodules are not supported')
                items.append((name.decode(), mode, oid))
    else:
        for record in git('ls-files', '--stage', '-z').split(b'\0'):
            if record:
                meta, name = record.split(b'\t', 1)
                mode, oid, stage = meta.decode().split()
                if stage != '0':
                    raise ValueError('Unresolved merge')
                items.append((name.decode(), mode, oid))
    if not items:
        raise ValueError('No tracked files to audit')
    blobs = {name: git('cat-file', 'blob', oid) for name, _, oid in items}
    manifest = blobs['manifests/groups/open.sha256'].decode()
    allowed = dict((line.split()[1], line.split()[0]) for line in manifest.splitlines())
    if len(allowed) != 9:
        raise ValueError('Expected exactly nine OFL fonts')
    errors = []
    # Patterns describe personal filesystem paths and credentials, not public upstream author notices.
    patterns = [
        (r'(?i)[a-z]:[\\/](?:Users|Documents and Settings)[\\/][^\s/\\"<>]+', 'personal Windows path'),
        (r'/(?:home|Users)/[a-zA-Z0-9_.-]+/', 'personal Unix path'),
        (r'(?i)\b(?:github_pat_|gh[pousr]_)[a-zA-Z0-9_]{20,}', 'GitHub token'),
        (r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', 'private key'),
        (r'(?i)AKIA[0-9A-Z]{16}', 'AWS key'),
    ]
    for name, mode, _ in items:
        p = Path(name)
        if not name.isascii(): errors.append((name, 'non-ASCII filename'))
        if mode not in {'100644', '100755'}: errors.append((name, 'symlink/submodule'))
        if any(part in {'logs', 'private', 'local', 'source_archives', 'build', 'dist', '__MACOSX', '__pycache__'} for part in p.parts):
            errors.append((name, 'private/generated directory'))
        if p.name.startswith('._') or p.name in {'.DS_Store', '.env', 'Thumbs.db'} or p.suffix.lower() in {'.log', '.zip', '.bak', '.key', '.pem', '.pyc'}:
            errors.append((name, 'private/generated file'))
        data = blobs[name]
        if name.startswith('fonts/'):
            if name not in allowed or hashlib.sha256(data).hexdigest() != allowed[name]:
                errors.append((name, 'font is not in the reviewed OFL manifest'))
            continue
        try:
            content = data.decode('utf-8')
        except UnicodeDecodeError:
            errors.append((name, 'unexpected binary file')); continue
        for pattern, reason in patterns:
            if re.search(pattern, content): errors.append((name, reason))
        if p.suffix in {'.sh', '.py', '.desktop'}:
            if '\r' in content: errors.append((name, 'CRLF executable'))
            if mode != '100755': errors.append((name, 'executable bit missing'))
    for name in allowed:
        if name not in blobs: errors.append((name, 'missing bundled font'))
    if errors:
        for name, reason in errors: print(f'FAIL {name}: {reason}', file=sys.stderr)
        return 1
    print(f'Public audit passed: {len(items)} tracked files; 9 OFL fonts; no forbidden paths, logs or detected credentials.')
    print('Automated patterns supplement manual review; they cannot prove that every possible secret is absent.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
